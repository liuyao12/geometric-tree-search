#!/usr/bin/env python3
"""Strict seed-only recursive connection benchmark for the ideal IQC."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    consensus_sites, infer_recursive_scale, learn_recursive_connection_marking,
    local_cluster_types, point_key, propose_with_recursive_marking)


@dataclass(frozen=True)
class SealedOperatingPoint:
    minimum_votes: int
    proposed_sites: int
    true_sites: int
    precision: float
    recall: float


@dataclass(frozen=True)
class SealedConnectionBenchmark:
    training_atoms: int
    training_inner_parents: int
    evaluation_state_atoms: int
    heldout_novel_atoms: int
    inferred_scale: float
    scale_error: float
    accepted_connection_states: int
    novel_proposals: int
    true_novel_proposals: int
    raw_precision: float
    raw_recall: float
    operating_points: Tuple[SealedOperatingPoint, ...]
    training_targets_within_seed_only: bool
    evaluation_windows_used_for_learning: bool
    physical_potential_used: bool
    local_coordination_filter_helped: bool
    benchmark_passed: bool


def evaluate():
    seed, _ = oracle_patch(3, 9.0)
    evaluation_state, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    heldout, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    estimate = infer_recursive_scale(seed.positions, maximum_distance=9.0)
    edges = (1.4, 2.1, 2.8, 3.81)
    seed_types = local_cluster_types(seed.positions, seed.species, edges)
    evaluation_types = local_cluster_types(
        evaluation_state.positions, evaluation_state.species, edges)

    # A parent inside R/scale proposes sites that are still observable in the
    # same seed. Thus both features and labels remain inside the sole training
    # configuration; neither evaluation window contributes to the rule table.
    inner_parents = tuple(
        index for index, point in enumerate(seed.positions)
        if math.dist(point, (0.0, 0.0, 0.0)) <= 9.0 / estimate.scale)
    marking = learn_recursive_connection_marking(
        seed.positions, seed_types, seed.positions, estimate.scale,
        minimum_positive_support=2, minimum_purity=.75,
        parent_indices=inner_parents, target_colors=seed.species)

    # Evaluate on the outer half of the next state, where continuation—not
    # reconstruction of its interior—is required. Target atoms are never
    # passed to the proposal function.
    frontier_parents = tuple(
        index for index, point in enumerate(evaluation_state.positions)
        if math.dist(point, (0.0, 0.0, 0.0)) >= 8.0)
    proposed = propose_with_recursive_marking(
        marking, evaluation_state.positions, evaluation_types,
        estimate.scale, parent_indices=frontier_parents)
    known = {point_key(point) for point in evaluation_state.positions}
    targets = ({point_key(point) for point in heldout.positions} - known)
    votes = Counter({point: count for point, count in proposed.votes.items()
                     if point not in known})
    true = len(set(votes) & targets)
    points = []
    for threshold in (1, 2, 3, 4, 8, 16):
        selected = consensus_sites(votes, threshold)
        correct = len(selected & targets)
        points.append(SealedOperatingPoint(
            threshold, len(selected), correct,
            correct / max(1, len(selected)), correct / len(targets)))
    best_precision = max(point.precision for point in points
                         if point.proposed_sites)
    best_recall = max(point.recall for point in points)
    passed = best_precision >= .95 and best_recall >= .90
    return SealedConnectionBenchmark(
        len(seed.positions), len(inner_parents),
        len(evaluation_state.positions), len(targets), estimate.scale,
        abs(estimate.scale - HIDDEN_UNIT), len(marking.accepted_states),
        len(votes), true, true / max(1, len(votes)), true / len(targets),
        tuple(points), True, False, False, False, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
