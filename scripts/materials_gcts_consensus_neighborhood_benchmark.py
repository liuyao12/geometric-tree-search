#!/usr/bin/env python3
"""Leakage-controlled second-order marking benchmark for ideal IQC growth."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_consensus_neighborhood import (
    fit_binned_consensus_neighborhood_marker,
    fit_consensus_neighborhood_marker,
    score_binned_consensus_neighborhoods, score_consensus_neighborhoods)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    MarkedProposalResult, learn_recursive_connection_marking,
    local_cluster_types, map_to_prototypes, point_key,
    propose_with_recursive_marking)


@dataclass(frozen=True)
class ScoreOperatingPoint:
    threshold: float
    proposed_sites: int
    true_sites: int
    false_sites: int
    precision: float
    coverage: float


@dataclass(frozen=True)
class CalibratedOperatingPoint:
    training_precision_floor: float
    selected_threshold: float
    heldout_proposed_sites: int
    heldout_true_sites: int
    heldout_false_sites: int
    heldout_precision: float
    heldout_coverage: float


@dataclass(frozen=True)
class BudgetOperatingPoint:
    budget_multiplier: float
    site_budget: int
    second_order_precision: float
    second_order_coverage: float
    binned_second_order_precision: float
    binned_second_order_coverage: float
    ensemble_precision: float
    ensemble_coverage: float
    vote_only_precision: float
    vote_only_coverage: float


@dataclass(frozen=True)
class ConsensusNeighborhoodBenchmark:
    atom_counts: Tuple[int, int, int]
    cross_fit_folds: int
    training_proposals: int
    training_positive_proposals: int
    heldout_proposals: int
    heldout_positive_proposals: int
    operating_points: Tuple[ScoreOperatingPoint, ...]
    calibrated_second_order: Tuple[CalibratedOperatingPoint, ...]
    calibrated_vote_only: Tuple[CalibratedOperatingPoint, ...]
    learned_atom_growth_factor: float
    predicted_next_atom_count: int
    budget_operating_points: Tuple[BudgetOperatingPoint, ...]
    trained_on_heldout_labels: bool
    second_order_marking: bool
    rigid_motion_invariant_descriptor: bool


def _spatial_fold(point) -> int:
    x, y, z = point
    return (int(x >= 0) + 2 * int(y >= 0) + 4 * int(z >= 0)) % 5


def _cross_fitted_training_votes(
        first, second, first_types, minimum_purity=.5,
        minimum_positive_support=2) -> MarkedProposalResult:
    folds = tuple(_spatial_fold(point) for point in first.positions)
    votes = Counter()
    color_votes = {}
    target_color_votes = {}
    state_votes = {}
    parent_votes = {}
    for heldout_fold in range(5):
        training_parents = tuple(index for index, fold in enumerate(folds)
                                 if fold != heldout_fold)
        validation_parents = tuple(index for index, fold in enumerate(folds)
                                   if fold == heldout_fold)
        marking = learn_recursive_connection_marking(
            first.positions, first_types, second.positions, HIDDEN_UNIT,
            minimum_purity=minimum_purity,
            minimum_positive_support=minimum_positive_support,
            parent_indices=training_parents,
            target_colors=second.species)
        result = propose_with_recursive_marking(
            marking, first.positions, first_types, 1.0,
            parent_indices=validation_parents)
        votes.update(result.votes)
        for point, counts in result.color_votes.items():
            color_votes.setdefault(point, Counter()).update(counts)
        for point, counts in result.target_color_votes.items():
            target_color_votes.setdefault(point, Counter()).update(counts)
        for point, counts in result.state_votes.items():
            state_votes.setdefault(point, Counter()).update(counts)
        for point, counts in result.parent_votes.items():
            parent_votes.setdefault(point, Counter()).update(counts)
    result = MarkedProposalResult(votes, sum(votes.values()), None,
                                  color_votes, target_color_votes,
                                  state_votes, parent_votes)
    return _without_known_sites(result, first.positions)


def _without_known_sites(result, known_positions):
    known = {point_key(point) for point in known_positions}
    kept = {point for point in result.votes if point not in known}
    votes = Counter({point: result.votes[point] for point in kept})
    return MarkedProposalResult(
        votes, sum(votes.values()), None,
        {point: result.color_votes[point] for point in kept},
        {point: result.target_color_votes[point] for point in kept},
        {point: result.state_votes[point] for point in kept},
        {point: result.parent_votes[point] for point in kept})


def _calibrated_threshold(scores, targets, precision_floor):
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    true = total = 0
    best = None
    index = 0
    while index < len(ordered):
        threshold = ordered[index][1]
        while index < len(ordered) and ordered[index][1] == threshold:
            true += ordered[index][0] in targets
            total += 1
            index += 1
        if true / total >= precision_floor:
            best = threshold
    return best if best is not None else float("inf")


def _apply_calibrated(scores, targets, floor, threshold):
    selected = {point for point, score in scores.items()
                if score >= threshold}
    true = len(selected & targets)
    return CalibratedOperatingPoint(
        floor, threshold, len(selected), true, len(selected) - true,
        true / len(selected) if selected else 0.0, true / len(targets))


def _top_budget(scores, targets, budget):
    selected = {point for point, _ in sorted(
        scores.items(), key=lambda item: (-item[1], item[0]))[:budget]}
    true = len(selected & targets)
    return true / len(selected), true / len(targets)


def _percentile_ranks(scores):
    ordered = sorted(scores.items(), key=lambda item: (item[1], item[0]))
    denominator = max(1, len(ordered) - 1)
    return {point: index / denominator
            for index, (point, _) in enumerate(ordered)}


def evaluate() -> ConsensusNeighborhoodBenchmark:
    first, _ = oracle_patch(3, 9.0)
    second, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    third, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    edges = (1.4, 2.1, 2.8, 3.81)
    first_types = local_cluster_types(first.positions, first.species, edges)
    second_types = local_cluster_types(second.positions, second.species, edges)
    training = _cross_fitted_training_votes(
        first, second, first_types)
    second_order = fit_consensus_neighborhood_marker(
        training.votes, second.positions,
        color_votes=training.color_votes,
        target_color_votes=training.target_color_votes,
        state_votes=training.state_votes)
    binned_second_order = fit_binned_consensus_neighborhood_marker(
        training.votes, second.positions,
        color_votes=training.color_votes,
        target_color_votes=training.target_color_votes,
        state_votes=training.state_votes)
    first_order = learn_recursive_connection_marking(
        first.positions, first_types, second.positions, HIDDEN_UNIT,
        minimum_purity=.5, target_colors=second.species)
    heldout = propose_with_recursive_marking(
        first_order, second.positions,
        map_to_prototypes(second_types, first_types), HIDDEN_UNIT)
    heldout = _without_known_sites(heldout, second.positions)
    scores = score_consensus_neighborhoods(
        second_order, heldout.votes, heldout.color_votes,
        heldout.target_color_votes, heldout.state_votes)
    binned_scores = score_binned_consensus_neighborhoods(
        binned_second_order, heldout.votes,
        heldout.color_votes, heldout.target_color_votes, heldout.state_votes)
    known_training = {point_key(point) for point in first.positions}
    known_heldout = {point_key(point) for point in second.positions}
    training_targets = ({point_key(point) for point in second.positions} -
                        known_training)
    targets = ({point_key(point) for point in third.positions} -
               known_heldout)
    training_scores = score_consensus_neighborhoods(
        second_order, training.votes,
        training.color_votes, training.target_color_votes,
        training.state_votes)
    points = []
    for threshold in (.10, .30, .50, .70, .80, .90, .92, .94, .96, .98, .99):
        selected = {point for point, score in scores.items()
                    if score >= threshold}
        true = len(selected & targets)
        points.append(ScoreOperatingPoint(
            threshold, len(selected), true, len(selected) - true,
            true / len(selected) if selected else 0.0,
            true / len(targets)))
    calibrated_second_order = []
    calibrated_vote_only = []
    heldout_vote_scores = {point: float(vote)
                           for point, vote in heldout.votes.items()}
    training_vote_scores = {point: float(vote)
                            for point, vote in training.votes.items()}
    for floor in (.50, .75, .90, .95):
        threshold = _calibrated_threshold(
            training_scores, training_targets, floor)
        calibrated_second_order.append(_apply_calibrated(
            scores, targets, floor, threshold))
        vote_threshold = _calibrated_threshold(
            training_vote_scores, training_targets, floor)
        calibrated_vote_only.append(_apply_calibrated(
            heldout_vote_scores, targets, floor, vote_threshold))
    growth_factor = len(second.positions) / len(first.positions)
    predicted_next_count = (round(len(second.positions) * growth_factor) -
                            len(second.positions))
    logistic_ranks = _percentile_ranks(scores)
    binned_ranks = _percentile_ranks(binned_scores)
    ensemble_scores = {
        point: (logistic_ranks[point] + binned_ranks[point]) / 2.0
        for point in scores}
    budget_points = []
    for multiplier in (.5, 1., 2.):
        budget = min(len(scores), round(predicted_next_count * multiplier))
        second_metrics = _top_budget(scores, targets, budget)
        binned_metrics = _top_budget(binned_scores, targets, budget)
        ensemble_metrics = _top_budget(ensemble_scores, targets, budget)
        vote_metrics = _top_budget(heldout_vote_scores, targets, budget)
        budget_points.append(BudgetOperatingPoint(
            multiplier, budget, *second_metrics, *binned_metrics,
            *ensemble_metrics, *vote_metrics))
    return ConsensusNeighborhoodBenchmark(
        (len(first.positions), len(second.positions), len(third.positions)), 5,
        len(training.votes), len(set(training.votes) & training_targets),
        len(heldout.votes), len(set(heldout.votes) & targets), tuple(points),
        tuple(calibrated_second_order), tuple(calibrated_vote_only),
        growth_factor, predicted_next_count, tuple(budget_points),
        False, True, True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
