#!/usr/bin/env python3
"""Two-wave spatial confirmation of the frozen continuous IQC section."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    score_regenerative_growth)
from materials_gcts_iqc_continuous_section_confirmation import (
    BEAM_WIDTH, CHANNEL_REACH, COMPLETED_TRAINING_CENTERS,
    CONFIRMATION_CENTER as FIRST_CONTINUOUS_CENTER, LOOKAHEAD_DEPTH,
    fit_continuous_section)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_persistent_frontier_beam import (
    run_persistent_frontier_beam)


CONFIRMATION_CENTER = (0., 50., 0.)
WAVES = 2


@dataclass(frozen=True)
class ContinuousSectionMultistepConfirmation:
    training_centers: tuple[tuple[float, float, float], ...]
    prior_confirmation_center: tuple[float, float, float]
    confirmation_center: tuple[float, float, float]
    continuous_model_digest: str
    model_matches_first_confirmation: bool
    channel_reach: int
    beam_width: int
    lookahead_depth: int
    requested_waves: int
    executed_waves: int
    minimum_prior_center_separation: float
    required_center_separation: float
    spatial_domains_disjoint: bool
    seed_atoms: int
    target_atoms: int
    candidate_bands_by_wave: tuple[int, ...]
    selected_paths: tuple[tuple[int, ...], ...]
    first_exact_ranks: tuple[int | None, ...]
    emitted_sites_by_wave: tuple[int, ...]
    correct_sites_by_wave: tuple[int, ...]
    false_sites_by_wave: tuple[int, ...]
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    frozen_execution_digest: str
    target_materialized_after_execution: bool
    target_used_for_selection: bool
    two_wave_spatial_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate():
    (prototypes, connection, seeds, targets, marker, refinement,
     _folds) = fit_continuous_section()
    model_digest = hashlib.sha256(repr((marker, refinement)).encode()).hexdigest()
    seed = _seed_crop(CONFIRMATION_CENTER)
    proposals = _bounded_proposals(
        connection, prototypes, seed, CONFIRMATION_CENTER)
    learned_factor = sum(len(target.positions) / len(seed_.positions)
                         for seed_, target in zip(seeds, targets)) / len(seeds)
    pool = min(len(proposals.votes), 2 * max(
        1, round(len(seed.positions) * learned_factor) - len(seed.positions)))
    rank_values = {rank: float(CHANNEL_REACH + 1 - rank)
                   for rank in range(1, CHANNEL_REACH + 1)}
    result = run_persistent_frontier_beam(
        marker, refinement, connection, proposals,
        seed.positions, seed.species, CLUSTER_EDGES, pool,
        CONFIRMATION_CENTER, EVALUATION_TARGET_RADIUS, waves=WAVES,
        beam_width=BEAM_WIDTH, branching_width=CHANNEL_REACH,
        lookahead_depth=LOOKAHEAD_DEPTH, root_rank_values=rank_values,
        candidate_snapshot_width=CHANNEL_REACH)
    frozen = hashlib.sha256(repr((model_digest, result)).encode()).hexdigest()

    # The new outer target first exists after both self-fed decisions freeze.
    target = _open_target(CONFIRMATION_CENTER)
    scored = score_regenerative_growth(
        result.records, result.traces, seed.positions,
        target.positions, target.species)
    target_colors = {tuple(round(value, 6) for value in point): color
                     for point, color in zip(target.positions,
                                             target.species)}
    exact_ranks = []
    for decision in result.decisions:
        truth = tuple((sum(
            target_colors.get(tuple(round(value, 6) for value in point)) ==
            color for point, color in zip(points, colors)), len(points))
            for points, colors in zip(decision.first_candidate_positions,
                                      decision.first_candidate_species))
        exact_ranks.append(next((rank for rank, (correct, total) in zip(
            decision.first_candidate_ranks, truth)
            if total and correct == total), None))
    prior = COMPLETED_TRAINING_CENTERS + (FIRST_CONTINUOUS_CENTER,)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    correct_by_wave = tuple(row.true_sites for row in scored)
    false_by_wave = tuple(row.false_sites for row in scored)
    emitted_by_wave = tuple(correct + false for correct, false in zip(
        correct_by_wave, false_by_wave))
    correct = sum(correct_by_wave)
    false = sum(false_by_wave)
    emitted = correct + false
    target_used = result.target_used_for_selection
    passed = bool(
        minimum > required and len(result.decisions) == WAVES and emitted and
        not false and not target_used and all(rank is not None
                                              for rank in exact_ranks) and
        all(decision.selected_path_ranks[0] == rank
            for decision, rank in zip(result.decisions, exact_ranks)))
    return ContinuousSectionMultistepConfirmation(
        COMPLETED_TRAINING_CENTERS, FIRST_CONTINUOUS_CENTER,
        CONFIRMATION_CENTER, model_digest,
        model_digest ==
        "bb891f2c5055afe529c77c2834632c4df654bb2c9c944b1a4ae888535d980697",
        CHANNEL_REACH, BEAM_WIDTH, LOOKAHEAD_DEPTH, WAVES,
        len(result.decisions), minimum, required, minimum > required,
        len(seed.positions), len(target.positions),
        tuple(len(row.first_candidate_ranks) for row in result.decisions),
        tuple(row.selected_path_ranks for row in result.decisions),
        tuple(exact_ranks), emitted_by_wave, correct_by_wave, false_by_wave,
        emitted, correct, false, correct / emitted if emitted else 0.,
        frozen, True, target_used, passed, False,
        ("continuous section transfers for two self-fed waves"
         if passed else
         "continuous section does not yet transfer for two self-fed waves"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
