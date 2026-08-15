#!/usr/bin/env python3
"""In-sample local-port marking diagnostic on dense NaCl replay.

Sparse macro admission and dense frozen-train matching define the candidate
actions.  A bounded zero-corona marking learns only connection observation
counts for each local parent-type port.  It has no position, world direction,
radius, target atom, cell, or material label.  Every arm enumerates the exact
same candidates; only ranking changes.  Shuffled controls permute learned
scores within parent type.

The dense matcher and port labels see all 216 atoms, including the later outer
score region.  This is therefore explicitly an in-sample reconstruction
diagnostic, not a guarded causal transfer result.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
import json
import math
import random
from statistics import median

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import (
    _compile_productions, _site_key, execute_macro_derivation,
    score_macro_derivation)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros


@dataclass(frozen=True)
class MatchedWork:
    arm: str
    accepted_placements: int
    proposals: int
    proposed_novel_atoms: int
    correct_novel_atoms: int
    wrong_placements: int
    wrong_novel_atoms: int
    geometric_backtracks: int
    candidate_checks: int
    precision: float
    heldout_recall: float


@dataclass(frozen=True)
class DenseNaClInSampleMarkingAudit:
    training_atoms: int
    seed_atoms: int
    heldout_atoms: int
    admitted_macro_types: int
    dense_macro_occurrences: int
    frozen_candidate_actions: int
    learned_parent_states: int
    learned_connection_labels: int
    matched_correct_novel_atoms: int
    marked: MatchedWork
    unmarked: MatchedWork
    shuffled_median_proposals: float
    shuffled_median_wrong_placements: float
    shuffled_median_backtracks: float
    shuffled_best_wrong_plus_backtracks: int
    shuffled_runs: int
    empirical_work_p_value: float
    identical_frozen_candidates: bool
    marking_fit_train_ports_only: bool
    global_radius_direction_target_unused_by_marking: bool
    in_sample_reconstruction_gate_passed: bool
    independent_outer_shell: bool
    integrated_as_default_policy: bool


def _score_labels(program):
    productions = _compile_productions(program)
    labels = {item.production_id: (
        item.training_observations + item.training_child_port_witnesses)
              for item in productions}
    parents = defaultdict(list)
    for item in productions:
        parents[item.parent_type].append(item.production_id)
    return productions, labels, parents


def _shuffled(labels, parents, seed):
    rng = random.Random(seed)
    result = dict(labels)
    for production_ids in parents.values():
        values = [labels[index] for index in production_ids]
        rng.shuffle(values)
        for index, value in zip(production_ids, values):
            result[index] = value
    return result


def _ranker(scores):
    return lambda parent, production, child, orbit, overlap, emitted: (
        -scores[production], -overlap, -emitted, production, parent)


def _curve(derivation, target_keys):
    proposed_atoms = correct = wrong_placements = 0
    curve = []
    for step_index, step in enumerate(derivation.steps, 1):
        emitted = step.certificate.emitted_sites
        proposed_atoms += len(emitted)
        step_correct = sum(key in target_keys for key in emitted)
        correct += step_correct
        wrong_placements += step_correct < len(emitted)
        curve.append((step_index, proposed_atoms, correct, wrong_placements))
    return tuple(curve)


def _prefix_for_correct(curve, required):
    return next(item for item in curve if item[2] >= required)


def evaluate(*, shuffled_runs: int = 31) -> DenseNaClInSampleMarkingAudit:
    if shuffled_runs < 3:
        raise ValueError("at least three shuffled controls are required")
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    admitted = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, admitted.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types)

    center = tuple(sum(point[axis] for point in nacl.positions) /
                   len(nacl.positions) for axis in range(3))
    radii = tuple(math.dist(point, center) for point in nacl.positions)
    cutoff = median(radii)
    inner = {index for index, radius in enumerate(radii) if radius <= cutoff}
    supports = dict(promoted.occurrence_supports)
    seeds = tuple(item for item in promoted.occurrences
                  if set(supports[item.occurrence_id]) <= inner)
    seed_sites = tuple((nacl.species[index], nacl.positions[index])
                       for index in sorted(inner))
    target_keys = {_site_key((species, point), .03)
                   for species, point in zip(nacl.species, nacl.positions)}
    productions, labels, parents = _score_labels(promoted)
    arms = [("unmarked", None), ("marked", _ranker(labels))]
    arms.extend((f"shuffle-{run}", _ranker(_shuffled(
        labels, parents, 1729 + run))) for run in range(shuffled_runs))

    maximum_runs = []
    for name, ranker in arms:
        derivation = execute_macro_derivation(
            promoted, seeds, explicit_seed_sites=seed_sites,
            maximum_levels=1, maximum_new_nodes_per_level=64, ranker=ranker)
        maximum_runs.append((name, ranker, derivation,
                             _curve(derivation, target_keys)))
    if any(not curve or curve[-1][2] <= 0
           for _, _, _, curve in maximum_runs):
        raise AssertionError("every arm must emit a correct heldout atom")
    matched_correct = min(curve[-1][2]
                          for _, _, _, curve in maximum_runs)

    results = []
    candidate_checks = {item.attempted_candidates
                        for _, _, item, _ in maximum_runs}
    for name, ranker, _, curve in maximum_runs:
        placements, _, _, _ = _prefix_for_correct(curve, matched_correct)
        replay = execute_macro_derivation(
            promoted, seeds, explicit_seed_sites=seed_sites,
            maximum_levels=1, maximum_new_nodes_per_level=placements,
            ranker=ranker)
        score = score_macro_derivation(
            replay, nacl.species, nacl.positions)
        wrong_placements = sum(any(key not in target_keys
                                   for key in step.certificate.emitted_sites)
                               for step in replay.steps)
        results.append(MatchedWork(
            name, placements,
            placements + replay.rejected_batch_conflicts,
            score.proposed_novel_atoms,
            score.correct_novel_atoms,
            wrong_placements,
            score.proposed_novel_atoms - score.correct_novel_atoms,
            replay.rejected_batch_conflicts, replay.attempted_candidates,
            score.precision, score.heldout_recall))
    by_name = {item.arm: item for item in results}
    marked = by_name["marked"]
    unmarked = by_name["unmarked"]
    shuffled = tuple(by_name[f"shuffle-{run}"]
                     for run in range(shuffled_runs))
    marked_work = marked.wrong_placements + marked.geometric_backtracks
    shuffled_work = tuple(item.wrong_placements + item.geometric_backtracks
                          for item in shuffled)
    empirical_p = ((1 + sum(value <= marked_work
                             for value in shuffled_work)) /
                   (shuffled_runs + 1))
    gate = (
        len(candidate_checks) == 1 and
        marked.proposals < unmarked.proposals and
        marked.proposals < median(item.proposals for item in shuffled) and
        marked_work < unmarked.wrong_placements +
        unmarked.geometric_backtracks and
        marked_work < median(shuffled_work) and
        marked.precision > unmarked.precision and empirical_p <= .05)
    return DenseNaClInSampleMarkingAudit(
        len(nacl.positions), len(seed_sites),
        len(nacl.positions) - len(seed_sites), len(admitted.macro_types),
        dense.total_dense_occurrences, next(iter(candidate_checks)),
        len(parents), len(productions), matched_correct, marked, unmarked,
        median(item.proposals for item in shuffled),
        median(item.wrong_placements for item in shuffled),
        median(item.geometric_backtracks for item in shuffled),
        min(shuffled_work), shuffled_runs,
        empirical_p, len(candidate_checks) == 1, True, True, gate,
        False, False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shuffles", type=int, default=31)
    arguments = parser.parse_args()
    result = evaluate(shuffled_runs=arguments.shuffles)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
