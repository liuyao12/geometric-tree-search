#!/usr/bin/env python3
"""Leakage-controlled recursive-frontier GCTS benchmark on the ideal IQC."""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_consensus_neighborhood_benchmark import (
    _cross_fitted_training_votes, _without_known_sites)
from materials_gcts_frontier_attachment import (
    fit_frontier_attachment_marker, score_frontier_attachments)
from materials_gcts_frontier_band_beam import FrontierBand, search_frontier_bands
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    MarkedProposalResult, learn_recursive_connection_marking, local_cluster_types,
    map_to_prototypes, merge_marked_proposal_results, point_key,
    propose_with_recursive_marking)


@dataclass(frozen=True)
class FrontierOperatingPoint:
    site_budget: int
    true_sites: int
    false_sites: int
    precision: float
    novel_coverage: float


@dataclass(frozen=True)
class ScoreLandmark:
    rank: int
    score: float


@dataclass(frozen=True)
class IterativeGrowthWave:
    wave: int
    plateau_sites: int
    true_sites: int
    false_sites: int
    cumulative_sites: int
    cumulative_precision: float
    cumulative_novel_coverage: float
    maximum_score: float
    frontier_candidates: int


@dataclass(frozen=True)
class RegenerativeGrowthTrace:
    wave: int
    positions: Tuple[Tuple[float, float, float], ...]
    species: Tuple[object, ...]


@dataclass(frozen=True)
class RegenerativeScoreBand:
    wave: int
    rank: int
    score: float
    sites: int
    true_sites: int
    false_sites: int
    hard_core_conflicts: int
    lookahead_maximum_score: float
    lookahead_plateau_sites: int
    lookahead_frontier_candidates: int
    positions: Tuple[Tuple[float, float, float], ...]
    species: Tuple[object, ...]


@dataclass(frozen=True)
class RegenerativeBeamDecision:
    wave: int
    selection_objective: str
    candidate_ranks: Tuple[int, ...]
    candidate_sites: Tuple[int, ...]
    candidate_positions: Tuple[Tuple[Point, ...], ...]
    candidate_species: Tuple[Tuple[object, ...], ...]
    current_scores: Tuple[float, ...]
    lookahead_scores: Tuple[float, ...]
    lookahead_plateau_sites: Tuple[int, ...]
    lookahead_frontier_candidates: Tuple[int, ...]
    candidate_true_sites: Tuple[int, ...]
    candidate_false_sites: Tuple[int, ...]
    selected_rank: int
    selected_sites: int
    selected_true_sites: int
    selected_false_sites: int
    greedy_rollback: int
    target_used_for_selection: bool


@dataclass(frozen=True)
class FrontierAttachmentBenchmark:
    atom_counts: Tuple[int, int, int]
    training_candidates: int
    training_novel_positives: int
    heldout_candidates: int
    heldout_novel_targets: int
    training_forced_prefix: int
    projected_forced_prefix: int
    projected_surface_factor: float
    projected_operating_point: FrontierOperatingPoint
    calibrated_score_threshold: float
    calibrated_operating_point: FrontierOperatingPoint
    diagnostic_operating_points: Tuple[FrontierOperatingPoint, ...]
    hard_core_operating_points: Tuple[FrontierOperatingPoint, ...]
    third_order_operating_points: Tuple[FrontierOperatingPoint, ...]
    training_provisional_pool: int
    heldout_provisional_pool: int
    third_order_training_pure_prefix: int
    third_order_projected_prefix: int
    third_order_projected_operating_point: FrontierOperatingPoint
    third_order_score_landmarks: Tuple[ScoreLandmark, ...]
    largest_top_score_gap_rank: int
    largest_top_score_gap: float
    iterative_growth_waves: Tuple[IterativeGrowthWave, ...]
    regenerative_growth_waves: Tuple[IterativeGrowthWave, ...]
    regenerative_growth_traces: Tuple[RegenerativeGrowthTrace, ...]
    regenerative_wave17_score_bands: Tuple[RegenerativeScoreBand, ...]
    regenerative_beam_decisions: Tuple[RegenerativeBeamDecision, ...]
    learned_envelope_scale: float
    regenerative_radius_limit: float
    learned_minimum_separation: float
    trained_on_heldout_labels: bool
    known_sites_are_features_not_labels: bool
    rigid_motion_invariant_descriptor: bool


def _operating_point(scores, targets, budget):
    selected = {point for point, _ in sorted(
        scores.items(), key=lambda item: (-item[1], item[0]))[:budget]}
    true = len(selected & targets)
    return FrontierOperatingPoint(
        len(selected), true, len(selected) - true,
        true / len(selected) if selected else 0.0, true / len(targets))


def _hard_core_prefix(scores, targets, known_positions, budget,
                      minimum_separation):
    cell = minimum_separation
    grid = {}
    for point in known_positions:
        key = tuple(int(value // cell) for value in point)
        grid.setdefault(key, []).append(point)
    selected = []
    for point in sorted(scores, key=lambda item: (-scores[item], item)):
        key = tuple(int(value // cell) for value in point)
        conflict = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for other in grid.get(
                            (key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if sum((left - right) ** 2
                               for left, right in zip(point, other)) < (
                                   minimum_separation ** 2 - 1e-8):
                            conflict = True
                            break
                    if conflict:
                        break
                if conflict:
                    break
            if conflict:
                break
        if conflict:
            continue
        selected.append(point)
        grid.setdefault(key, []).append(point)
        if len(selected) >= budget:
            break
    true = len(set(selected) & targets)
    return FrontierOperatingPoint(
        len(selected), true, len(selected) - true,
        true / len(selected) if selected else 0.0, true / len(targets))


def _largest_prefix_at_precision(scores, targets, precision_floor):
    ordered = sorted(scores, key=lambda point: (-scores[point], point))
    true = 0
    best = 0
    for index, point in enumerate(ordered, 1):
        true += point in targets
        if true / index >= precision_floor:
            best = index
    return best


def _lowest_threshold_at_precision(scores, targets, precision_floor):
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    true = 0
    best = float("inf")
    for index, (point, score) in enumerate(ordered, 1):
        true += point in targets
        if true / index >= precision_floor:
            best = score
    return best


def _candidate_fold(point):
    x, y, z = point
    return (int(x >= 0) + 2 * int(y >= 0) + 4 * int(z >= 0)) % 5


def _subset_proposals(proposals, selected):
    points = set(selected)
    votes = Counter({point: proposals.votes[point] for point in points})
    return MarkedProposalResult(
        votes, sum(votes.values()), None,
        {point: proposals.color_votes[point] for point in points},
        {point: proposals.target_color_votes[point] for point in points},
        {point: proposals.state_votes[point] for point in points},
        {point: proposals.parent_votes[point] for point in points},
        None if proposals.causal_endpoint_votes is None else
        {point: proposals.causal_endpoint_votes[point] for point in points})


def _cross_fitted_frontier_scores(training, known, known_colors, targets):
    folds = {point: _candidate_fold(point) for point in training.votes}
    scores = {}
    for heldout_fold in range(5):
        fit_points = [point for point, fold in folds.items()
                      if fold != heldout_fold]
        validation_points = [point for point, fold in folds.items()
                             if fold == heldout_fold]
        marker = fit_frontier_attachment_marker(
            _subset_proposals(training, fit_points), known, known_colors,
            targets)
        scores.update(score_frontier_attachments(
            marker, _subset_proposals(training, validation_points),
            known, known_colors))
    return scores


def _cross_fitted_refinement_scores(
        training, augmented_known, augmented_colors, targets):
    folds = {point: _candidate_fold(point) for point in training.votes}
    scores = {}
    for heldout_fold in range(5):
        fit_points = [point for point, fold in folds.items()
                      if fold != heldout_fold]
        validation_points = [point for point, fold in folds.items()
                             if fold == heldout_fold]
        marker = fit_frontier_attachment_marker(
            _subset_proposals(training, fit_points),
            augmented_known, augmented_colors, targets)
        scores.update(score_frontier_attachments(
            marker, _subset_proposals(training, validation_points),
            augmented_known, augmented_colors))
    return scores


def _dominant_source_color(proposals, point):
    counts = proposals.color_votes[point]
    encoded = min(counts, key=lambda color: (-counts[color], color))
    try:
        return ast.literal_eval(encoded)
    except (ValueError, SyntaxError):
        return encoded


def _augmented_frontier(proposals, scores, known_positions, known_colors,
                        pool_size):
    pool = sorted(scores, key=lambda point: (-scores[point], point))[:pool_size]
    positions = tuple(known_positions) + tuple(pool)
    colors = tuple(known_colors) + tuple(
        _dominant_source_color(proposals, point) for point in pool)
    return positions, colors


def _iterative_maximum_plateaus(
        frontier_marker, refinement_marker, proposals, known_positions,
        known_colors, targets, provisional_pool, waves=8):
    remaining = proposals
    accepted = []
    accepted_true = 0
    current_positions = list(known_positions)
    current_colors = list(known_colors)
    records = []
    for wave in range(1, waves + 1):
        frontier_scores = score_frontier_attachments(
            frontier_marker, remaining, current_positions, current_colors)
        augmented = _augmented_frontier(
            remaining, frontier_scores, current_positions, current_colors,
            min(provisional_pool, len(frontier_scores)))
        scores = score_frontier_attachments(
            refinement_marker, remaining, *augmented)
        maximum = max(scores.values())
        plateau = tuple(sorted(point for point, score in scores.items()
                               if maximum - score <= 1e-12))
        true = sum(point in targets for point in plateau)
        accepted.extend(plateau)
        accepted_true += true
        records.append(IterativeGrowthWave(
            wave, len(plateau), true, len(plateau) - true, len(accepted),
            accepted_true / len(accepted), accepted_true / len(targets),
            maximum, len(scores)))
        current_positions.extend(plateau)
        current_colors.extend(_dominant_source_color(remaining, point)
                              for point in plateau)
        remaining = _without_known_sites(remaining, plateau)
        if not remaining.votes:
            break
    return tuple(records)


def _center_and_radius(positions):
    center = tuple(sum(point[axis] for point in positions) / len(positions)
                   for axis in range(3))
    radius = max(sum((point[axis] - center[axis]) ** 2
                     for axis in range(3)) ** .5 for point in positions)
    return center, radius


def _regenerative_maximum_plateaus(
        frontier_marker, refinement_marker, connection_marker, proposals,
        known_positions, known_colors, cluster_edges, targets,
        provisional_pool, center, radius_limit, waves=8,
        beam_start_wave=None, beam_width=2, diagnostic_waves=(17,),
        beam_objective="leaf-score"):
    if beam_start_wave is not None and (beam_start_wave < 1 or beam_width < 2):
        raise ValueError("beam execution requires a positive start and width >= 2")
    if beam_objective not in ("leaf-score", "frontier-supply"):
        raise ValueError("unknown beam objective")
    if targets is None and diagnostic_waves:
        raise ValueError("truth diagnostics require posthoc targets")
    truth_available = targets is not None
    def within(point):
        return sum((point[axis] - center[axis]) ** 2
                   for axis in range(3)) ** .5 <= radius_limit + 1e-8

    def advance(positions, colors, source_remaining, plateau, plateau_colors):
        branch_positions = list(positions) + list(plateau)
        branch_colors = list(colors) + list(plateau_colors)
        old_count = len(positions)
        new_indices = tuple(range(old_count, len(branch_positions)))
        all_indices = tuple(range(len(branch_positions)))
        old_indices = tuple(range(old_count))
        updated_types = local_cluster_types(
            tuple(branch_positions), tuple(branch_colors), cluster_edges)
        new_parents = propose_with_recursive_marking(
            connection_marker, tuple(branch_positions), updated_types,
            HIDDEN_UNIT, parent_indices=new_indices,
            source_indices=all_indices)
        old_parents_new_sources = propose_with_recursive_marking(
            connection_marker, tuple(branch_positions), updated_types,
            HIDDEN_UNIT, parent_indices=old_indices,
            source_indices=new_indices)
        following = _without_known_sites(source_remaining, plateau)
        following = merge_marked_proposal_results(
            (following, new_parents, old_parents_new_sources))
        following = _without_known_sites(following, branch_positions)
        following = _subset_proposals(
            following, (point for point in following.votes if within(point)))
        return branch_positions, branch_colors, following

    remaining = _subset_proposals(
        proposals, (point for point in proposals.votes if within(point)))
    accepted = []
    accepted_true = 0
    current_positions = list(known_positions)
    current_colors = list(known_colors)
    records = []
    traces = []
    diagnostic_bands = []
    beam_decisions = []
    for wave in range(1, waves + 1):
        frontier_scores = score_frontier_attachments(
            frontier_marker, remaining, current_positions, current_colors)
        augmented = _augmented_frontier(
            remaining, frontier_scores, current_positions, current_colors,
            min(provisional_pool, len(frontier_scores)))
        scores = score_frontier_attachments(
            refinement_marker, remaining, *augmented)
        diagnostic_wave = wave in diagnostic_waves
        beam_wave = beam_start_wave is not None and wave >= beam_start_wave
        # These rows deliberately exclude target membership. The beam commits
        # from this frozen evidence before any posthoc truth is attached.
        band_rows = []
        if diagnostic_wave or beam_wave:
            minimum_separation = min(
                sum((left - right) ** 2 for left, right in zip(point, other))
                ** .5
                for index, point in enumerate(known_positions)
                for other in known_positions[index + 1:])
            levels = sorted(set(scores.values()), reverse=True)[:max(
                12 if diagnostic_wave else 0, beam_width if beam_wave else 0)]
            for rank, level in enumerate(levels, 1):
                band = tuple(point for point, score in scores.items()
                             if abs(score - level) <= 1e-12)
                band_colors = tuple(
                    _dominant_source_color(remaining, point)
                    for point in band)
                conflicts = sum(
                    0 < sum((left - right) ** 2
                            for left, right in zip(point, other)) ** .5 <
                    minimum_separation - 1e-8
                    for index, point in enumerate(band)
                    for other in tuple(current_positions) + band[index + 1:])
                next_maximum = 0.0
                next_plateau = 0
                next_candidates = 0
                if rank <= max(2 if diagnostic_wave else 0,
                               beam_width if beam_wave else 0):
                    branch_positions, branch_colors, branch_remaining = advance(
                        current_positions, current_colors, remaining,
                        band, band_colors)
                    if branch_remaining.votes:
                        next_frontier = score_frontier_attachments(
                            frontier_marker, branch_remaining,
                            branch_positions, branch_colors)
                        next_augmented = _augmented_frontier(
                            branch_remaining, next_frontier,
                            branch_positions, branch_colors,
                            min(provisional_pool, len(next_frontier)))
                        next_scores = score_frontier_attachments(
                            refinement_marker, branch_remaining,
                            *next_augmented)
                        next_maximum = max(next_scores.values())
                        next_plateau = sum(
                            next_maximum - score <= 1e-12
                            for score in next_scores.values())
                        next_candidates = len(next_scores)
                band_rows.append((rank, level, band, band_colors, conflicts,
                                  next_maximum, next_plateau,
                                  next_candidates))
        selected_rank = 1
        greedy_rollback = 0
        if beam_wave:
            choice_rows = tuple(band_rows[:beam_width])
            evidence = tuple((row[0], row[1], row[5])
                             for row in choice_rows)
            roots = tuple(FrontierBand(rank, current, 0.)
                          for rank, current, _future in evidence)
            if beam_objective == "frontier-supply":
                future = {row[0]: (FrontierBand(
                    f"future-{wave}-{row[0]}", row[5], float(row[7])),)
                    for row in choice_rows}
            else:
                future = {rank: (FrontierBand(
                    f"future-{wave}-{rank}", 0., value),)
                    for rank, _current, value in evidence}
            beam_trace = search_frontier_bands(
                roots, lambda band: future.get(band.band_id, ()),
                beam_width=beam_width, lookahead_depth=2,
                leaf_boundary_first=True)
            selected_rank = int(beam_trace.selected_ids[0])
            greedy_rollback = beam_trace.greedy_rollbacks
        maximum = (band_rows[selected_rank - 1][1]
                   if beam_wave else max(scores.values()))
        plateau = tuple(sorted(point for point, score in scores.items()
                               if abs(maximum - score) <= 1e-12))
        true = (sum(point in targets for point in plateau)
                if truth_available else -1)
        if diagnostic_wave:
            for (rank, level, band, band_colors, conflicts, next_maximum,
                 next_plateau, next_candidates) in band_rows:
                band_true = sum(point in targets for point in band)
                diagnostic_bands.append(RegenerativeScoreBand(
                    wave, rank, level, len(band), band_true,
                    len(band) - band_true, conflicts, next_maximum,
                    next_plateau, next_candidates, band, band_colors))
        if beam_wave:
            choice_rows = tuple(band_rows[:beam_width])
            candidate_true = (tuple(
                sum(point in targets for point in row[2])
                for row in choice_rows) if truth_available else ())
            beam_decisions.append(RegenerativeBeamDecision(
                wave, beam_objective, tuple(row[0] for row in choice_rows),
                tuple(len(row[2]) for row in choice_rows),
                tuple(row[2] for row in choice_rows),
                tuple(row[3] for row in choice_rows),
                tuple(row[1] for row in choice_rows),
                tuple(row[5] for row in choice_rows),
                tuple(row[6] for row in choice_rows),
                tuple(row[7] for row in choice_rows), candidate_true,
                (tuple(len(row[2]) - count for row, count in
                       zip(choice_rows, candidate_true))
                 if truth_available else ()),
                selected_rank, len(plateau), true,
                len(plateau) - true if truth_available else -1,
                greedy_rollback, False))
        accepted.extend(plateau)
        if truth_available:
            accepted_true += true
        plateau_colors = tuple(
            _dominant_source_color(remaining, point) for point in plateau)
        records.append(IterativeGrowthWave(
            wave, len(plateau), true,
            len(plateau) - true if truth_available else -1, len(accepted),
            (accepted_true / len(accepted) if truth_available else
             float("nan")),
            (accepted_true / len(targets) if truth_available else
             float("nan")),
            maximum, len(scores)))
        traces.append(RegenerativeGrowthTrace(
            wave, plateau, plateau_colors))

        current_positions, current_colors, remaining = advance(
            current_positions, current_colors, remaining,
            plateau, plateau_colors)
        if not remaining.votes:
            break
    return (tuple(records), tuple(traces), tuple(diagnostic_bands),
            tuple(beam_decisions))


def score_regenerative_growth(
        records, traces, known_positions, target_positions, target_species):
    """Attach colored-site truth only after a target-blind trace is frozen."""
    if (len(records) != len(traces) or
            len(target_positions) != len(target_species) or
            any(len(trace.positions) != len(trace.species)
                for trace in traces) or
            any(record.wave != trace.wave
                for record, trace in zip(records, traces))):
        raise ValueError("growth records, traces, and target must align")
    known = {point_key(point) for point in known_positions}
    target = {point_key(point): species
              for point, species in zip(target_positions, target_species)}
    novel_targets = set(target) - known
    accepted = set()
    accepted_true = 0
    scored = []
    for record, trace in zip(records, traces):
        true = false = 0
        for point, species in zip(trace.positions, trace.species):
            key = point_key(point)
            if key in accepted:
                continue
            accepted.add(key)
            if key in novel_targets and target[key] == species:
                true += 1
            else:
                false += 1
        accepted_true += true
        scored.append(IterativeGrowthWave(
            record.wave, true + false, true, false, len(accepted),
            accepted_true / len(accepted) if accepted else 0.,
            accepted_true / len(novel_targets) if novel_targets else 0.,
            record.maximum_score, record.frontier_candidates))
    return tuple(scored)


def evaluate(regenerative_wave_count: int = 8, *, beam_start_wave=None,
             beam_width: int = 2, diagnostic_waves=(17,),
             beam_objective="leaf-score") \
        -> FrontierAttachmentBenchmark:
    if regenerative_wave_count < 1:
        raise ValueError("regenerative wave count must be positive")
    first, _ = oracle_patch(3, 9.0)
    second, _ = oracle_patch(4, 9.0 * HIDDEN_UNIT)
    third, _ = oracle_patch(6, 9.0 * HIDDEN_UNIT ** 2)
    cluster_edges = (1.4, 2.1, 2.8, 3.81)
    first_types = local_cluster_types(
        first.positions, first.species, cluster_edges)
    second_types = local_cluster_types(
        second.positions, second.species, cluster_edges)
    training = _cross_fitted_training_votes(first, second, first_types)
    known_first = {point_key(point) for point in first.positions}
    training_targets = ({point_key(point) for point in second.positions} -
                        known_first)
    marker = fit_frontier_attachment_marker(
        training, first.positions, first.species, training_targets)
    training_scores = _cross_fitted_frontier_scores(
        training, first.positions, first.species, training_targets)

    connection_marking = learn_recursive_connection_marking(
        first.positions, first_types, second.positions, HIDDEN_UNIT,
        minimum_purity=.5, target_colors=second.species)
    heldout = propose_with_recursive_marking(
        connection_marking, second.positions,
        map_to_prototypes(second_types, first_types), HIDDEN_UNIT)
    heldout = _without_known_sites(heldout, second.positions)
    heldout_scores = score_frontier_attachments(
        marker, heldout, second.positions, second.species)
    known_second = {point_key(point) for point in second.positions}
    heldout_targets = ({point_key(point) for point in third.positions} -
                       known_second)

    training_pool = min(len(training_scores), 2 * len(training_targets))
    heldout_predicted_novel = (
        round(len(second.positions) * len(second.positions) /
              len(first.positions)) - len(second.positions))
    heldout_pool = min(len(heldout_scores), 2 * heldout_predicted_novel)
    augmented_training = _augmented_frontier(
        training, training_scores, first.positions, first.species,
        training_pool)
    refinement_marker = fit_frontier_attachment_marker(
        training, *augmented_training, training_targets)
    refinement_training_scores = _cross_fitted_refinement_scores(
        training, *augmented_training, training_targets)
    augmented_heldout = _augmented_frontier(
        heldout, heldout_scores, second.positions, second.species,
        heldout_pool)
    refinement_scores = score_frontier_attachments(
        refinement_marker, heldout, *augmented_heldout)

    training_prefix = _largest_prefix_at_precision(
        training_scores, training_targets, .99)
    score_threshold = _lowest_threshold_at_precision(
        training_scores, training_targets, .99)
    surface_factor = HIDDEN_UNIT ** 2
    projected_prefix = max(1, round(training_prefix * surface_factor))
    projected = _operating_point(
        heldout_scores, heldout_targets, projected_prefix)
    calibrated_sites = {point: score for point, score in heldout_scores.items()
                        if score >= score_threshold}
    calibrated = _operating_point(
        calibrated_sites, heldout_targets, len(calibrated_sites))
    diagnostic = tuple(_operating_point(
        heldout_scores, heldout_targets, min(budget, len(heldout_scores)))
        for budget in (250, 500, 1000, 2000, 2839, 5678))
    minimum_separation = min(
        sum((left - right) ** 2 for left, right in zip(point, other)) ** .5
        for index, point in enumerate(second.positions)
        for other in second.positions[index + 1:])
    hard_core = tuple(_hard_core_prefix(
        heldout_scores, heldout_targets, second.positions, budget,
        minimum_separation) for budget in (250, 500, 1000, 2000))
    third_order = tuple(_operating_point(
        refinement_scores, heldout_targets,
        min(budget, len(refinement_scores)))
        for budget in (250, 500, 1000, 2000, 2839, 5678))
    third_training_prefix = _largest_prefix_at_precision(
        refinement_training_scores, training_targets, 1.0)
    third_projected_prefix = max(
        1, round(third_training_prefix * surface_factor))
    third_projected = _operating_point(
        refinement_scores, heldout_targets, third_projected_prefix)
    ordered_refinement_scores = sorted(refinement_scores.values(), reverse=True)
    landmarks = tuple(ScoreLandmark(
        rank, ordered_refinement_scores[rank - 1])
        for rank in (1, 10, 50, 100, 250, 251, 500, 1000)
        if rank <= len(ordered_refinement_scores))
    gap_rank, gap = max(
        ((index, ordered_refinement_scores[index - 1] -
          ordered_refinement_scores[index])
         for index in range(1, min(2000, len(ordered_refinement_scores)))),
        key=lambda item: (item[1], -item[0]))
    iterative_waves = _iterative_maximum_plateaus(
        marker, refinement_marker, heldout, second.positions, second.species,
        heldout_targets, heldout_pool)
    first_center, first_radius = _center_and_radius(first.positions)
    second_center, second_radius = _center_and_radius(second.positions)
    envelope_scale = second_radius / first_radius
    regenerative_limit = second_radius * envelope_scale
    (regenerative_waves, regenerative_traces, regenerative_bands,
     regenerative_beam_decisions) = \
        _regenerative_maximum_plateaus(
        marker, refinement_marker, connection_marking, heldout,
        second.positions, second.species, cluster_edges, heldout_targets,
        heldout_pool, second_center, regenerative_limit,
        waves=regenerative_wave_count, beam_start_wave=beam_start_wave,
        beam_width=beam_width, diagnostic_waves=diagnostic_waves,
        beam_objective=beam_objective)
    return FrontierAttachmentBenchmark(
        (len(first.positions), len(second.positions), len(third.positions)),
        len(training.votes), len(training_targets), len(heldout.votes),
        len(heldout_targets), training_prefix, projected_prefix,
        surface_factor, projected, score_threshold, calibrated,
        diagnostic, hard_core, third_order, training_pool, heldout_pool,
        third_training_prefix, third_projected_prefix, third_projected,
        landmarks, gap_rank, gap,
        iterative_waves, regenerative_waves, regenerative_traces,
        regenerative_bands, regenerative_beam_decisions,
        envelope_scale,
        regenerative_limit,
        minimum_separation, False, True, True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--regenerative-waves", type=int, default=8)
    parser.add_argument("--beam-start-wave", type=int)
    parser.add_argument("--beam-width", type=int, default=2)
    parser.add_argument("--beam-objective", choices=(
        "leaf-score", "frontier-supply"), default="leaf-score")
    arguments = parser.parse_args()
    result = evaluate(arguments.regenerative_waves,
                      beam_start_wave=arguments.beam_start_wave,
                      beam_width=arguments.beam_width,
                      beam_objective=arguments.beam_objective)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
