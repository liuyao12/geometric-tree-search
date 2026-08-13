#!/usr/bin/env python3
"""Matched-quality causal ablation on an actual IQC growth frontier."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass, replace
from statistics import median
from typing import Tuple

from materials_gcts_consensus_neighborhood_benchmark import (
    _cross_fitted_training_votes, _without_known_sites)
from materials_gcts_frontier_attachment import (
    fit_frontier_attachment_marker, score_frontier_attachments)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types,
    map_to_prototypes, point_key, propose_with_recursive_marking)


@dataclass(frozen=True)
class SearchArm:
    name: str
    correct_target: int
    proposal_checks: int
    failed_branches: int
    precision_at_stop: float


@dataclass(frozen=True)
class FrontierSearchAblation:
    training_atoms: int
    known_frontier_atoms: int
    heldout_oracle_atoms: int
    training_candidates: int
    heldout_candidates: int
    heldout_novel_targets: int
    matched_correct_sites: int
    marked: SearchArm
    overlap_vote_baseline: SearchArm
    shuffled_runs: int
    shuffled_checks: Tuple[int, ...]
    shuffled_median_checks: float
    shuffled_best_checks: int
    marked_vs_overlap_reduction: float
    marked_vs_shuffle_median_reduction: float
    marking_beats_every_shuffle: bool
    heldout_labels_used_for_training: bool
    candidate_set_identical: bool
    benchmark_passed: bool


def _work_to_correct(order, targets, correct_target):
    correct = 0
    for checked, point in enumerate(order, 1):
        correct += point in targets
        if correct >= correct_target:
            return SearchArm("", correct_target, checked, checked - correct,
                             correct / checked)
    raise RuntimeError("candidate order cannot reach matched correct target")


def _shuffle_targets(points, targets, seed):
    labels = [point in targets for point in points]
    random.Random(seed).shuffle(labels)
    return {point for point, label in zip(points, labels) if label}


def evaluate(shuffled_runs=30):
    first, _ = oracle_patch(3, 9.0)
    second, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    third, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    edges = (1.4, 2.1, 2.8, 3.81)
    first_types = local_cluster_types(first.positions, first.species, edges)
    second_types = local_cluster_types(second.positions, second.species, edges)
    training = _cross_fitted_training_votes(first, second, first_types)
    known_first = {point_key(point) for point in first.positions}
    training_targets = ({point_key(point) for point in second.positions} -
                        known_first)
    marker = fit_frontier_attachment_marker(
        training, first.positions, first.species, training_targets)

    connection = learn_recursive_connection_marking(
        first.positions, first_types, second.positions, HIDDEN_UNIT,
        minimum_purity=.5, target_colors=second.species)
    heldout = propose_with_recursive_marking(
        connection, second.positions,
        map_to_prototypes(second_types, first_types), HIDDEN_UNIT)
    heldout = _without_known_sites(heldout, second.positions)
    heldout_scores = score_frontier_attachments(
        marker, heldout, second.positions, second.species)
    known_second = {point_key(point) for point in second.positions}
    heldout_targets = ({point_key(point) for point in third.positions} -
                       known_second)
    marked_order = tuple(sorted(
        heldout.votes, key=lambda point: (-heldout_scores[point], point)))
    maximum = heldout_scores[marked_order[0]]
    maximum_plateau = tuple(point for point in marked_order
                            if maximum - heldout_scores[point] <= 1e-12)
    correct_target = sum(point in heldout_targets for point in maximum_plateau)
    if correct_target == 0 or correct_target != len(maximum_plateau):
        raise RuntimeError("maximum marked plateau is not a pure forced move")
    vote_order = tuple(sorted(
        heldout.votes, key=lambda point: (-heldout.votes[point], point)))
    marked = _work_to_correct(marked_order, heldout_targets, correct_target)
    baseline = _work_to_correct(vote_order, heldout_targets, correct_target)

    training_points = tuple(sorted(training.votes))
    shuffled_checks = []
    for run in range(shuffled_runs):
        shuffled_marker = fit_frontier_attachment_marker(
            training, first.positions, first.species,
            _shuffle_targets(training_points, training_targets,
                             1009 + 7919 * run), epochs=160)
        shuffled_scores = score_frontier_attachments(
            shuffled_marker, heldout, second.positions, second.species)
        order = tuple(sorted(
            heldout.votes, key=lambda point: (-shuffled_scores[point], point)))
        shuffled_checks.append(_work_to_correct(
            order, heldout_targets, correct_target).proposal_checks)
    shuffled_checks = tuple(shuffled_checks)
    marked = replace(marked, name="learned incoming GCTS marking")
    baseline = replace(baseline, name="overlap-vote baseline")
    passed = (marked.proposal_checks < baseline.proposal_checks and
              marked.proposal_checks < min(shuffled_checks))
    return FrontierSearchAblation(
        len(first.positions), len(second.positions), len(third.positions),
        len(training.votes), len(heldout.votes), len(heldout_targets),
        correct_target, marked, baseline, shuffled_runs, shuffled_checks,
        median(shuffled_checks), min(shuffled_checks),
        baseline.proposal_checks / marked.proposal_checks,
        median(shuffled_checks) / marked.proposal_checks,
        marked.proposal_checks < min(shuffled_checks), False, True, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shuffles", type=int, default=30)
    arguments = parser.parse_args()
    result = evaluate(arguments.shuffles)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
