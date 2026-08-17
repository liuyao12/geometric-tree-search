#!/usr/bin/env python3
"""Spatially disjoint transfer of the frozen IQC option-preserving beam.

The marking and recursive connection grammar are fitted only on concentric
origin windows. Execution starts from a radius-9 crop around a requested
off-origin centre, with a public radius-9*tau boundary. The outer crop is
generated only after the target-free trace and branch decisions are immutable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_consensus_neighborhood_benchmark import (
    _cross_fitted_training_votes)
from materials_gcts_frontier_attachment import (
    fit_frontier_attachment_marker, score_frontier_attachments)
from materials_gcts_frontier_attachment_benchmark import (
    _augmented_frontier, _cross_fitted_frontier_scores,
    _dominant_source_color, _regenerative_maximum_plateaus,
    _subset_proposals, _without_known_sites,
    score_regenerative_growth)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import (
    HIDDEN_UNIT, oracle_patch, oracle_patch_fast)
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types,
    map_to_prototypes, propose_with_recursive_marking)


TRAIN_INNER_RADIUS = 9.0
TRAIN_OUTER_RADIUS = TRAIN_INNER_RADIUS * HIDDEN_UNIT
EVALUATION_CENTER = (30.0, 0.0, 0.0)
EVALUATION_SEED_RADIUS = 9.0
EVALUATION_TARGET_RADIUS = EVALUATION_SEED_RADIUS * HIDDEN_UNIT
CLUSTER_EDGES = (1.4, 2.1, 2.8, 3.81)


@dataclass(frozen=True)
class SpatialBeamTransferBenchmark:
    training_inner_atoms: int
    training_outer_atoms: int
    evaluation_seed_atoms: int
    evaluation_target_atoms: int
    evaluation_novel_target_atoms: int
    evaluation_center: tuple[float, float, float]
    beam_width: int
    center_separation: float
    summed_outer_radii: float
    spatial_domains_disjoint: bool
    initial_frozen_candidates: int
    initial_bounded_candidates: int
    initial_geometrically_correct_candidates: int
    initial_colored_correct_candidates: int
    first_score_band_with_correct_site: int | None
    first_pure_correct_score_band: int | None
    candidate_universe_digest: str
    requested_waves: int
    executed_waves: int
    selected_ranks: tuple[int, ...]
    first_wave_candidate_true_sites: tuple[int, ...]
    first_wave_candidate_false_sites: tuple[int, ...]
    first_exact_candidate_rank: int | None
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    novel_recall: float
    candidate_supply: tuple[int, ...]
    execution_digest: str
    target_materialized_after_execution: bool
    raw_execution_truth_fields_unavailable: bool
    target_used_for_selection: bool
    independent_growth_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _crop(configuration, center, radius, name):
    indices = tuple(index for index, point in enumerate(configuration.positions)
                    if math.dist(point, center) <= radius + 1e-10)
    return AtomicConfiguration(
        name, tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices))


def _seed_crop(center):
    # The chosen radius contains the entire evaluation seed.  Although the generator
    # necessarily visits other points, only this detached crop escapes scope.
    oracle, _ = oracle_patch_fast(
        12, math.ceil(math.dist((0., 0., 0.), center) +
                      EVALUATION_SEED_RADIUS))
    return _crop(oracle, center, EVALUATION_SEED_RADIUS,
                 "IQC-spatial-beam-seed")


def _open_target(center):
    oracle, _ = oracle_patch_fast(
        12, math.ceil(math.dist((0., 0., 0.), center) +
                      EVALUATION_TARGET_RADIUS))
    return _crop(oracle, center, EVALUATION_TARGET_RADIUS,
                 "IQC-spatial-beam-target")


def evaluate(waves: int = 8, *, evaluation_center=EVALUATION_CENTER,
             beam_width: int = 4) -> SpatialBeamTransferBenchmark:
    center = tuple(float(value) for value in evaluation_center)
    if (waves < 1 or beam_width < 2 or len(center) != 3 or
            not all(math.isfinite(value) for value in center)):
        raise ValueError("waves, beam width, and evaluation center are invalid")
    first, _ = oracle_patch(3, TRAIN_INNER_RADIUS)
    second, _ = oracle_patch(4, TRAIN_OUTER_RADIUS)
    first_types = local_cluster_types(
        first.positions, first.species, CLUSTER_EDGES)
    training = _cross_fitted_training_votes(first, second, first_types)
    known_first = {tuple(round(value, 6) for value in point)
                   for point in first.positions}
    training_targets = {
        tuple(round(value, 6) for value in point) for point in second.positions
    } - known_first
    marker = fit_frontier_attachment_marker(
        training, first.positions, first.species, training_targets)
    training_scores = _cross_fitted_frontier_scores(
        training, first.positions, first.species, training_targets)
    connection = learn_recursive_connection_marking(
        first.positions, first_types, second.positions, HIDDEN_UNIT,
        minimum_purity=.5, target_colors=second.species)
    training_pool = min(len(training_scores), 2 * len(training_targets))
    augmented_training = _augmented_frontier(
        training, training_scores, first.positions, first.species,
        training_pool)
    refinement = fit_frontier_attachment_marker(
        training, *augmented_training, training_targets)

    seed = _seed_crop(center)
    seed_types = local_cluster_types(
        seed.positions, seed.species, CLUSTER_EDGES)
    proposals = propose_with_recursive_marking(
        connection, seed.positions,
        map_to_prototypes(seed_types, first_types), HIDDEN_UNIT)
    proposals = _without_known_sites(proposals, seed.positions)
    initial_scores = score_frontier_attachments(
        marker, proposals, seed.positions, seed.species)
    learned_population_factor = len(second.positions) / len(first.positions)
    predicted_novel = max(1, round(
        len(seed.positions) * learned_population_factor) - len(seed.positions))
    pool = min(len(initial_scores), 2 * predicted_novel)
    bounded = _subset_proposals(proposals, (
        point for point in proposals.votes
        if math.dist(point, center) <=
        EVALUATION_TARGET_RADIUS + 1e-8))
    bounded_frontier_scores = score_frontier_attachments(
        marker, bounded, seed.positions, seed.species)
    bounded_augmented = _augmented_frontier(
        bounded, bounded_frontier_scores, seed.positions, seed.species,
        min(pool, len(bounded_frontier_scores)))
    bounded_refinement_scores = score_frontier_attachments(
        refinement, bounded, *bounded_augmented)
    candidate_universe = tuple(sorted(
        (point, _dominant_source_color(bounded, point),
         bounded_refinement_scores[point]) for point in bounded.votes))
    candidate_universe_digest = hashlib.sha256(
        repr(candidate_universe).encode()).hexdigest()

    records, traces, diagnostics, decisions = \
        _regenerative_maximum_plateaus(
            marker, refinement, connection, proposals,
            seed.positions, seed.species, CLUSTER_EDGES, None, pool,
            center, EVALUATION_TARGET_RADIUS, waves=waves,
            beam_start_wave=1, beam_width=beam_width, diagnostic_waves=(),
            beam_objective="frontier-supply")
    if diagnostics:
        raise AssertionError("sealed execution produced truth diagnostics")
    frozen_payload = (
        tuple((trace.wave, trace.positions, trace.species) for trace in traces),
        tuple((row.wave, row.selection_objective, row.candidate_ranks,
               row.candidate_positions, row.candidate_species,
               row.current_scores, row.lookahead_scores,
               row.lookahead_frontier_candidates, row.selected_rank)
              for row in decisions))
    digest = hashlib.sha256(repr(frozen_payload).encode()).hexdigest()

    # This is the first call that materializes the scoring annulus.
    target = _open_target(center)
    scored = score_regenerative_growth(
        records, traces, seed.positions, target.positions, target.species)
    known = {tuple(round(value, 6) for value in point)
             for point in seed.positions}
    target_keys = {tuple(round(value, 6) for value in point)
                   for point in target.positions}
    novel_targets = len(target_keys - known)
    target_colors = {
        tuple(round(value, 6) for value in point): species
        for point, species in zip(target.positions, target.species)}
    geometrically_correct = sum(
        tuple(round(value, 6) for value in point) in target_colors
        for point, _species, _score in candidate_universe)
    colored_correct = sum(
        tuple(round(value, 6) for value in point) in target_colors and
        target_colors[tuple(round(value, 6) for value in point)] == species
        for point, species, _score in candidate_universe)
    levels = tuple(sorted({score for _point, _species, score
                           in candidate_universe}, reverse=True))
    first_with_correct = first_pure = None
    for rank, level in enumerate(levels, 1):
        band = tuple(row for row in candidate_universe
                     if abs(row[2] - level) <= 1e-12)
        correct_band = sum(
            tuple(round(value, 6) for value in point) in target_colors and
            target_colors[tuple(round(value, 6) for value in point)] == species
            for point, species, _score in band)
        if correct_band and first_with_correct is None:
            first_with_correct = rank
        if correct_band == len(band) and first_pure is None:
            first_pure = rank
    first_decision = decisions[0]
    candidate_true = tuple(sum(
        tuple(round(value, 6) for value in point) in target_colors and
        target_colors[tuple(round(value, 6) for value in point)] == species
        for point, species in zip(positions, colors))
        for positions, colors in zip(
            first_decision.candidate_positions,
            first_decision.candidate_species))
    candidate_false = tuple(total - true for total, true in zip(
        first_decision.candidate_sites, candidate_true))
    first_exact = next((rank for rank, true, false in zip(
        first_decision.candidate_ranks, candidate_true, candidate_false)
                        if true > 0 and false == 0), None)
    correct = sum(item.true_sites for item in scored)
    false = sum(item.false_sites for item in scored)
    emitted = correct + false
    disjoint = math.dist((0., 0., 0.), center) > (
        TRAIN_OUTER_RADIUS + EVALUATION_TARGET_RADIUS)
    target_used = any(item.target_used_for_selection for item in decisions)
    raw_unscored = all(item.true_sites == item.false_sites == -1
                       for item in records) and all(
        item.selected_true_sites == item.selected_false_sites == -1 and
        not item.candidate_true_sites and not item.candidate_false_sites
        for item in decisions)
    passed = (disjoint and len(scored) >= 3 and emitted > 0 and false == 0 and
              not target_used and raw_unscored)
    return SpatialBeamTransferBenchmark(
        len(first.positions), len(second.positions), len(seed.positions),
        len(target.positions), novel_targets, center, beam_width,
        math.dist((0., 0., 0.), center),
        TRAIN_OUTER_RADIUS + EVALUATION_TARGET_RADIUS, disjoint,
        len(initial_scores), len(candidate_universe), geometrically_correct,
        colored_correct, first_with_correct, first_pure,
        candidate_universe_digest, waves, len(scored),
        tuple(item.selected_rank for item in decisions), candidate_true,
        candidate_false, first_exact, emitted, correct, false,
        correct / emitted if emitted else 0.,
        correct / novel_targets if novel_targets else 0.,
        tuple(item.frontier_candidates for item in records), digest, True,
        raw_unscored, target_used, passed, False,
        ("spatially disjoint option-preserving IQC growth is exact"
         if passed else
         "spatially disjoint option-preserving IQC growth remains red"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--waves", type=int, default=8)
    parser.add_argument("--beam-width", type=int, default=4)
    parser.add_argument("--center", type=float, nargs=3,
                        default=EVALUATION_CENTER)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.waves, evaluation_center=arguments.center,
                      beam_width=arguments.beam_width)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
