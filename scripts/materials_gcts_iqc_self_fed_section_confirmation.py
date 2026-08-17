#!/usr/bin/env python3
"""Train on known post-commit IQC frontiers, confirm two fresh waves."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment import (
    FrontierAttachmentExample, fit_frontier_attachment_marker_examples,
    score_frontier_attachments)
from materials_gcts_frontier_attachment_benchmark import (
    _augmented_frontier, _dominant_source_color,
    score_regenerative_growth)
from materials_gcts_iqc_continuous_section_confirmation import (
    BEAM_WIDTH, CHANNEL_REACH, COMPLETED_TRAINING_CENTERS,
    CONFIRMATION_CENTER as FIRST_CONTINUOUS_CENTER, LOOKAHEAD_DEPTH,
    fit_continuous_section)
from materials_gcts_iqc_continuous_section_multistep_confirmation import (
    CONFIRMATION_CENTER as FAILED_MULTISTEP_CENTER)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration, run_persistent_frontier_beam)


CONFIRMATION_CENTER = (-50., 0., 0.)
WAVES = 2


@dataclass(frozen=True)
class SelfFedSectionConfirmation:
    training_centers: tuple[tuple[float, float, float], ...]
    confirmation_center: tuple[float, float, float]
    base_model_digest: str
    base_model_matches_published: bool
    self_fed_model_digest: str
    teacher_forced_nuclei: int
    teacher_first_exact_ranks: tuple[int, ...]
    self_fed_training_examples: int
    self_fed_training_colored_positives: int
    channel_reach: int
    beam_width: int
    lookahead_depth: int
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


def _target_colors(target):
    return {tuple(round(value, 6) for value in point): color
            for point, color in zip(target.positions, target.species)}


def _band_truth(proposals, band, target):
    colors = _target_colors(target)
    correct = sum(
        colors.get(tuple(round(value, 6) for value in point)) ==
        _dominant_source_color(proposals, point) for point in band)
    return correct, len(band) - correct


def fit_self_fed_section():
    (prototypes, connection, seeds, targets, base_marker, base_refinement,
     _folds) = fit_continuous_section()
    states = []
    ranks = []
    for center, seed, target in zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        scores = score_frontier_attachments(
            base_marker, proposals, seed.positions, seed.species)
        known = {tuple(round(value, 6) for value in point)
                 for point in seed.positions}
        novel = sum(tuple(round(value, 6) for value in point) not in known
                    for point in target.positions)
        augmented = _augmented_frontier(
            proposals, scores, seed.positions, seed.species,
            min(len(scores), 2 * novel))
        refined = score_frontier_attachments(
            base_refinement, proposals, *augmented)
        levels = sorted(set(refined.values()), reverse=True)[:CHANNEL_REACH]
        chosen = None
        for rank, level in enumerate(levels, 1):
            band = tuple(sorted(point for point, value in refined.items()
                                if abs(value - level) <= 1e-12))
            correct, false = _band_truth(proposals, band, target)
            if correct and not false:
                chosen = rank, band
                break
        if chosen is None:
            continue
        rank, band = chosen
        band_colors = tuple(_dominant_source_color(proposals, point)
                            for point in band)
        positions, colors, remaining = advance_frontier_configuration(
            connection, proposals, seed.positions, seed.species,
            band, band_colors, CLUSTER_EDGES, center,
            EVALUATION_TARGET_RADIUS)
        if not remaining.votes:
            continue
        ranks.append(rank)
        states.append((remaining, positions, colors, target))
    examples = tuple(FrontierAttachmentExample(
        proposals, tuple(positions), tuple(colors), tuple(target.positions),
        tuple(target.species))
        for proposals, positions, colors, target in states)
    if len(examples) < 2:
        raise ValueError("self-fed section needs multiple training nuclei")
    marker = fit_frontier_attachment_marker_examples(examples)
    augmented_examples = []
    for proposals, positions, colors, target in states:
        scores = score_frontier_attachments(
            marker, proposals, positions, colors)
        known = {tuple(round(value, 6) for value in point)
                 for point in positions}
        novel = sum(tuple(round(value, 6) for value in point) not in known
                    for point in target.positions)
        augmented = _augmented_frontier(
            proposals, scores, positions, colors,
            min(len(scores), 2 * novel))
        augmented_examples.append(FrontierAttachmentExample(
            proposals, tuple(augmented[0]), tuple(augmented[1]),
            tuple(target.positions), tuple(target.species)))
    refinement = fit_frontier_attachment_marker_examples(
        tuple(augmented_examples))
    return (prototypes, connection, seeds, targets, base_marker,
            base_refinement, marker, refinement, tuple(ranks))


def evaluate():
    (prototypes, connection, seeds, targets, base_marker, base_refinement,
     self_marker, self_refinement, teacher_ranks) = fit_self_fed_section()
    base_digest = hashlib.sha256(
        repr((base_marker, base_refinement)).encode()).hexdigest()
    self_digest = hashlib.sha256(
        repr((self_marker, self_refinement)).encode()).hexdigest()
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
        base_marker, base_refinement, connection, proposals,
        seed.positions, seed.species, CLUSTER_EDGES, pool,
        CONFIRMATION_CENTER, EVALUATION_TARGET_RADIUS, waves=WAVES,
        beam_width=BEAM_WIDTH, branching_width=CHANNEL_REACH,
        lookahead_depth=LOOKAHEAD_DEPTH, root_rank_values=rank_values,
        candidate_snapshot_width=CHANNEL_REACH,
        frontier_markers_by_depth=(base_marker, self_marker),
        refinement_markers_by_depth=(base_refinement, self_refinement))
    frozen_digest = hashlib.sha256(
        repr((base_digest, self_digest, result)).encode()).hexdigest()

    # First construction of this outer target follows both frozen decisions.
    target = _open_target(CONFIRMATION_CENTER)
    scored = score_regenerative_growth(
        result.records, result.traces, seed.positions,
        target.positions, target.species)
    exact_ranks = []
    target_color = _target_colors(target)
    for decision in result.decisions:
        truth = tuple((sum(
            target_color.get(tuple(round(value, 6) for value in point)) ==
            color for point, color in zip(points, colors)), len(points))
            for points, colors in zip(decision.first_candidate_positions,
                                      decision.first_candidate_species))
        exact_ranks.append(next((rank for rank, (correct, total) in zip(
            decision.first_candidate_ranks, truth)
            if total and correct == total), None))
    prior = COMPLETED_TRAINING_CENTERS + (
        FIRST_CONTINUOUS_CENTER, FAILED_MULTISTEP_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    correct_by_wave = tuple(row.true_sites for row in scored)
    false_by_wave = tuple(row.false_sites for row in scored)
    emitted_by_wave = tuple(a + b for a, b in zip(
        correct_by_wave, false_by_wave))
    correct, false = sum(correct_by_wave), sum(false_by_wave)
    emitted = correct + false
    target_used = result.target_used_for_selection
    passed = bool(
        minimum > required and len(result.decisions) == WAVES and emitted and
        not false and not target_used and all(rank is not None
                                              for rank in exact_ranks) and
        all(decision.selected_path_ranks[0] == rank
            for decision, rank in zip(result.decisions, exact_ranks)))
    return SelfFedSectionConfirmation(
        COMPLETED_TRAINING_CENTERS, CONFIRMATION_CENTER,
        base_digest, base_digest ==
        "bb891f2c5055afe529c77c2834632c4df654bb2c9c944b1a4ae888535d980697",
        self_digest, len(teacher_ranks), teacher_ranks,
        self_marker.training_examples, self_marker.training_positives,
        CHANNEL_REACH, BEAM_WIDTH, LOOKAHEAD_DEPTH, minimum, required,
        minimum > required, len(seed.positions), len(target.positions),
        tuple(len(row.first_candidate_ranks) for row in result.decisions),
        tuple(row.selected_path_ranks for row in result.decisions),
        tuple(exact_ranks), emitted_by_wave, correct_by_wave, false_by_wave,
        emitted, correct, false, correct / emitted if emitted else 0.,
        frozen_digest, True, target_used, passed, False,
        ("self-fed continuous section transfers for two waves"
         if passed else
         "self-fed continuous section remains spatially red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
