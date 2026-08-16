#!/usr/bin/env python3
"""Sealed IQC benchmark for cluster-decoration tree search."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median

from materials_gcts_decoration_tree_search import (
    DecorationSearchPolicy, compile_decoration_problem,
    fit_decoration_marking, search_decoration_cover)
from materials_gcts_geometry_decoration_vocabulary_benchmark import (
    _decorations, _target_geometry_atlas)
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)
from materials_gcts_recurrent_macro_execution_benchmark import (
    compile_disjoint_iqc_execution_fixture)


@dataclass(frozen=True)
class SearchArm:
    strategy: str
    inferred_outer_atoms: int
    correct_outer_atoms: int
    wrong_outer_atoms: int
    precision: float
    recall: float
    selected_actions: int
    expanded_nodes: int
    conflict_rejections: int
    beam_pruned_states: int
    reached_fixed_point: bool


@dataclass(frozen=True)
class DecorationTreeSearchAudit:
    training_atoms: int
    evaluation_atoms: int
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
    target_positions_supplied_for_reconstruction: bool
    outer_species_used_during_search: bool
    target_used_by_search_api: bool
    gcts_beats_modal: bool
    gcts_beats_shuffles: bool
    reconstruction_gate_passed: bool
    autonomous_growth_claimed: bool
    limitation: str


def _shuffle_occurrence_decorations(values, seed):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for occurrence_id, (geometry_type, decoration_id) in values.items():
        groups[geometry_type].append((occurrence_id, decoration_id))
    result = {}
    for geometry_type, rows in sorted(groups.items()):
        labels = [label for _occurrence, label in rows]
        rng.shuffle(labels)
        for (occurrence_id, _old), label in zip(rows, labels):
            result[occurrence_id] = (geometry_type, label)
    return result


def _arm(trace, seed_atoms, target_species):
    labels = dict(trace.labelled_species)
    inferred = {atom: species for atom, species in labels.items()
                if atom not in seed_atoms}
    correct = sum(species == repr(target_species[atom])
                  for atom, species in inferred.items())
    wrong = len(inferred) - correct
    outer_count = len(target_species) - len(seed_atoms)
    return SearchArm(
        trace.policy.strategy, len(inferred), correct, wrong,
        correct / max(1, len(inferred)), correct / max(1, outer_count),
        len(trace.selected_actions), trace.expanded_nodes,
        trace.conflict_rejections, trace.beam_pruned_states,
        trace.reached_fixed_point)


def evaluate(shuffle_trials=0, minimum_marking_probability=.99,
             minimum_overlap_atoms=6):
    fixture, open_target = compile_disjoint_iqc_execution_fixture()
    train_species = tuple(species for species, _point in fixture.training_sites)
    train_positions = tuple(point for _species, point in fixture.training_sites)
    geometry = compile_irregular_port_program(
        tuple("*" for _ in train_positions), train_positions)
    train_decorations = _decorations(
        geometry, train_species, train_positions, geometry.occurrences,
        geometry.occurrence_supports)
    alternatives = defaultdict(set)
    observations_by_key = Counter(train_decorations)
    for geometry_type, decoration in train_decorations:
        alternatives[geometry_type].add(decoration)
    alternatives = {key: tuple(sorted(value))
                    for key, value in alternatives.items()}
    decoration_ids = {
        (geometry_type, decoration): index
        for index, (geometry_type, decoration) in enumerate(
            (item for geometry_type, values in sorted(alternatives.items())
             for item in ((geometry_type, decoration)
                          for decoration in values)))}
    decoration_observations = {
        (geometry_type, decoration_ids[geometry_type, decoration]): count
        for (geometry_type, decoration), count in observations_by_key.items()}
    occurrence_decorations = {
        occurrence.occurrence_id:
        (geometry_type, decoration_ids[geometry_type, decoration])
        for occurrence, (geometry_type, decoration) in zip(
            geometry.occurrences, train_decorations)}
    marking = fit_decoration_marking(
        occurrence_decorations, geometry.atlas.relation_classes)

    # Positions are part of this reconstruction task.  Species remain captured
    # behind a zero-argument scorer closure until every search arm is frozen.
    sealed_target = open_target()
    target_positions = sealed_target.positions
    open_species = lambda species=sealed_target.species: species
    enumeration = enumerate_frozen_port_occurrences(
        geometry, tuple("*" for _ in target_positions), target_positions)
    target_atlas = _target_geometry_atlas(geometry, enumeration)
    problem = compile_decoration_problem(
        target_positions, enumeration.occurrences,
        dict(enumeration.occurrence_supports),
        {item.type_id: item for item in geometry.prototypes}, alternatives,
        decoration_ids, decoration_observations,
        target_atlas.relation_classes)
    seed_species = {
        atom: repr(species)
        for atom, (species, point) in enumerate(
            zip(sealed_target.species, target_positions))
        if math.dist(point, fixture.boundary.origin) <= 7. + 1e-10}
    # Drop the direct object reference before executing.  The search receives
    # only positions through `problem` and the explicit inner seed labels.
    del sealed_target

    policy_common = dict(
        beam_width=12, maximum_depth=64,
        maximum_branches_per_state=12,
        minimum_overlap_atoms=minimum_overlap_atoms,
        marking_weight=.35, overlap_weight=.02,
        minimum_marking_probability=minimum_marking_probability)
    modal_trace = search_decoration_cover(
        problem, seed_species, marking,
        DecorationSearchPolicy("modal", **policy_common))
    gcts_trace = search_decoration_cover(
        problem, seed_species, marking,
        DecorationSearchPolicy("gcts", **policy_common))
    shuffled_traces = []
    for trial in range(shuffle_trials):
        shuffled = _shuffle_occurrence_decorations(
            occurrence_decorations, 9137 + trial)
        shuffled_marking = fit_decoration_marking(
            shuffled, geometry.atlas.relation_classes)
        shuffled_traces.append(search_decoration_cover(
            problem, seed_species, shuffled_marking,
            DecorationSearchPolicy("gcts", **policy_common)))

    target_species = open_species()
    modal = _arm(modal_trace, seed_species, target_species)
    gcts = _arm(gcts_trace, seed_species, target_species)
    shuffled = tuple(_arm(trace, seed_species, target_species)
                     for trace in shuffled_traces)
    shuffled_precision = tuple(item.precision for item in shuffled)
    shuffled_correct = tuple(item.correct_outer_atoms for item in shuffled)
    p_precision = ((1 + sum(value >= gcts.precision
                            for value in shuffled_precision)) /
                   (1 + len(shuffled))) if shuffled else 1.
    p_correct = ((1 + sum(value >= gcts.correct_outer_atoms
                          for value in shuffled_correct)) /
                 (1 + len(shuffled))) if shuffled else 1.
    identical = all(trace.candidate_digest == problem.candidate_digest
                    for trace in (modal_trace, gcts_trace) +
                    tuple(shuffled_traces))
    beats_modal = (gcts.correct_outer_atoms > modal.correct_outer_atoms and
                   gcts.precision >= modal.precision)
    beats_shuffles = bool(shuffled) and p_precision <= .05 and p_correct <= .05
    gate = gcts.precision >= .99 and gcts.recall >= .9 and beats_shuffles
    return DecorationTreeSearchAudit(
        len(train_positions), len(target_positions), len(seed_species),
        len(target_positions) - len(seed_species), len(geometry.prototypes),
        sum(map(len, alternatives.values())), len(enumeration.occurrences),
        len(problem.actions), problem.candidate_digest, modal, gcts,
        shuffle_trials, median(shuffled_precision) if shuffled else 0.,
        max(shuffled_precision, default=0.),
        median(shuffled_correct) if shuffled else 0., p_precision, p_correct,
        identical, True, False,
        modal_trace.target_used or gcts_trace.target_used or
        any(trace.target_used for trace in shuffled_traces),
        beats_modal, beats_shuffles, gate, False,
        "This is bounded species reconstruction on supplied coordinates. "
        "Every arm receives identical frozen geometry/decoration actions; "
        "GCTS changes only train-frozen ranking/admission. Autonomous growth and exponential "
        "recurrence require a separate target-blind coordinate emitter.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shuffle-trials", type=int, default=0)
    parser.add_argument("--minimum-marking-probability", type=float,
                        default=.99)
    parser.add_argument("--minimum-overlap-atoms", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.shuffle_trials, args.minimum_marking_probability,
                      args.minimum_overlap_atoms)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
