#!/usr/bin/env python3
"""Bounded GCTS decoration search on disjoint published Cd--Yb crops."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_cdyb_oracle import generate_cdyb
from materials_gcts_cdyb_partial_decoration_benchmark import (
    EVAL_CENTER, RADIUS, TRAIN_CENTERS)
from materials_gcts_decoration_tree_search import (
    DecorationSearchPolicy, compile_decoration_problem,
    fit_decoration_marking, search_decoration_cover)
from materials_gcts_decoration_tree_search_benchmark import (
    SearchArm, _arm, _shuffle_occurrence_decorations)
from materials_gcts_geometry_decoration_vocabulary_benchmark import (
    _decorations, _target_geometry_atlas)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)


@dataclass(frozen=True)
class CdYbDecorationTreeSearchAudit:
    train_atoms: int
    eval_atoms: int
    raw_atom_ids_disjoint: bool
    seed_atoms: int
    outer_atoms: int
    geometry_types: int
    decoration_alternatives: int
    frozen_geometry_occurrences: int
    frozen_decoration_actions: int
    candidate_digest: str
    modal: SearchArm
    gcts: SearchArm
    shuffle_trials: int
    shuffled_median_precision: float
    shuffled_best_precision: float
    shuffled_median_correct_atoms: float
    gcts_precision_empirical_p: float
    gcts_correct_atoms_empirical_p: float
    identical_candidate_digest_all_arms: bool
    target_labels_used_during_compile_or_search: bool
    source_sites_internal_coordinates_or_family_label_used: bool
    gcts_beats_modal: bool
    gcts_beats_shuffles: bool
    reconstruction_gate_passed: bool
    autonomous_growth_claimed: bool
    limitation: str


def evaluate(shuffle_trials=0, minimum_overlap_atoms=5):
    atoms = generate_cdyb(4, (60.,) * 3)
    train_ids = tuple(index for index, point in enumerate(atoms.positions)
                      if any(math.dist(center, point) <= RADIUS
                             for center in TRAIN_CENTERS))
    eval_ids = tuple(index for index, point in enumerate(atoms.positions)
                     if math.dist(EVAL_CENTER, point) <= RADIUS)
    train_positions = tuple(atoms.positions[index] for index in train_ids)
    train_species = tuple(atoms.symbols[index] for index in train_ids)
    eval_positions = tuple(atoms.positions[index] for index in eval_ids)
    eval_species = tuple(atoms.symbols[index] for index in eval_ids)

    geometry = compile_irregular_port_program(
        tuple("*" for _ in train_positions), train_positions)
    train_rows = _decorations(
        geometry, train_species, train_positions, geometry.occurrences,
        geometry.occurrence_supports)
    alternatives = defaultdict(set)
    observations = Counter(train_rows)
    for type_id, decoration in train_rows:
        alternatives[type_id].add(decoration)
    alternatives = {key: tuple(sorted(value))
                    for key, value in alternatives.items()}
    decoration_ids = {
        (type_id, decoration): index
        for index, (type_id, decoration) in enumerate(
            (item for type_id, values in sorted(alternatives.items())
             for item in ((type_id, decoration) for decoration in values)))}
    decoration_observations = {
        (type_id, decoration_ids[type_id, decoration]): count
        for (type_id, decoration), count in observations.items()}
    occurrence_decorations = {
        occurrence.occurrence_id:
        (type_id, decoration_ids[type_id, decoration])
        for occurrence, (type_id, decoration) in zip(
            geometry.occurrences, train_rows)}
    marking = fit_decoration_marking(
        occurrence_decorations, geometry.atlas.relation_classes)

    enumeration = enumerate_frozen_port_occurrences(
        geometry, tuple("*" for _ in eval_positions), eval_positions)
    target_atlas = _target_geometry_atlas(geometry, enumeration)
    problem = compile_decoration_problem(
        eval_positions, enumeration.occurrences,
        dict(enumeration.occurrence_supports),
        {item.type_id: item for item in geometry.prototypes}, alternatives,
        decoration_ids, decoration_observations,
        target_atlas.relation_classes)
    seed_species = {
        atom: repr(eval_species[atom])
        for atom, point in enumerate(eval_positions)
        if math.dist(EVAL_CENTER, point) <= 7. + 1e-10}
    common = dict(
        beam_width=12, maximum_depth=64,
        maximum_branches_per_state=12,
        minimum_overlap_atoms=minimum_overlap_atoms,
        marking_weight=.35, overlap_weight=.02,
        minimum_marking_probability=.99)
    modal_trace = search_decoration_cover(
        problem, seed_species, marking,
        DecorationSearchPolicy("modal", **common))
    gcts_trace = search_decoration_cover(
        problem, seed_species, marking,
        DecorationSearchPolicy("gcts", **common))
    shuffled_traces = []
    for trial in range(shuffle_trials):
        shuffled = _shuffle_occurrence_decorations(
            occurrence_decorations, 72191 + trial)
        shuffled_marking = fit_decoration_marking(
            shuffled, geometry.atlas.relation_classes)
        shuffled_traces.append(search_decoration_cover(
            problem, seed_species, shuffled_marking,
            DecorationSearchPolicy("gcts", **common)))
    modal = _arm(modal_trace, seed_species, eval_species)
    gcts = _arm(gcts_trace, seed_species, eval_species)
    shuffled = tuple(_arm(trace, seed_species, eval_species)
                     for trace in shuffled_traces)
    precisions = tuple(item.precision for item in shuffled)
    correct = tuple(item.correct_outer_atoms for item in shuffled)
    p_precision = ((1 + sum(value >= gcts.precision for value in precisions)) /
                   (1 + len(precisions))) if precisions else 1.
    p_correct = ((1 + sum(value >= gcts.correct_outer_atoms
                          for value in correct)) /
                 (1 + len(correct))) if correct else 1.
    identical = all(trace.candidate_digest == problem.candidate_digest
                    for trace in (modal_trace, gcts_trace) +
                    tuple(shuffled_traces))
    beats_modal = (gcts.precision >= modal.precision and
                   gcts.correct_outer_atoms > modal.correct_outer_atoms)
    # Precision is already at the mathematical ceiling in every arm.  The
    # causal question is therefore additional correct reach at no precision
    # loss, not an impossible improvement above 100% precision.
    beats_shuffles = (bool(shuffled) and p_correct <= .05 and
                      gcts.precision >= max(precisions))
    gate = gcts.precision >= .99 and gcts.recall >= .9 and beats_shuffles
    return CdYbDecorationTreeSearchAudit(
        len(train_ids), len(eval_ids),
        not set(train_ids).intersection(eval_ids), len(seed_species),
        len(eval_positions) - len(seed_species), len(geometry.prototypes),
        sum(map(len, alternatives.values())), len(enumeration.occurrences),
        len(problem.actions), problem.candidate_digest, modal, gcts,
        shuffle_trials, median(precisions) if precisions else 0.,
        max(precisions, default=0.), median(correct) if correct else 0.,
        p_precision, p_correct, identical, False, False, beats_modal,
        beats_shuffles, gate, False,
        "The search receives exact positions, an inner colored seed and "
        "train-frozen alternatives/markings. Evaluation labels are scorer-only; "
        "this is reconstruction, not autonomous coordinate growth.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shuffle-trials", type=int, default=0)
    parser.add_argument("--minimum-overlap-atoms", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.shuffle_trials, args.minimum_overlap_atoms)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
