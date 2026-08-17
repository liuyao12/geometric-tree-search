#!/usr/bin/env python3
"""Freeze a colored continuous GCTS section, then test a fresh IQC nucleus.

All training nuclei were opened by earlier completed spatial diagnostics.  The
confirmation centre is declared here and its outer target is not constructed
until the continuous section and persistent-beam trace are immutable.
"""

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
    _augmented_frontier, _dominant_source_color, score_regenerative_growth)
from materials_gcts_iqc_channel_count_confirmation import (
    CONFIRMATION_CENTER as EIGHTH_CENTER)
from materials_gcts_iqc_contextual_value_confirmation import (
    CONFIRMATION_CENTER as NINTH_CENTER)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    CONFIRMATION_CENTER as FOURTH_CENTER, TRAINING_CENTERS,
    _bounded_proposals)
from materials_gcts_iqc_rank_value_confirmation import (
    CONFIRMATION_CENTER as SIXTH_CENTER)
from materials_gcts_iqc_robust_persistent_beam_confirmation import (
    CONFIRMATION_CENTER as FIFTH_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_iqc_three_context_confirmation import (
    CONFIRMATION_CENTER as TENTH_CENTER)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_persistent_frontier_beam import (
    run_persistent_frontier_beam)
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types)


COMPLETED_TRAINING_CENTERS = (
    TRAINING_CENTERS + (FOURTH_CENTER, FIFTH_CENTER, SIXTH_CENTER,
                        EIGHTH_CENTER, NINTH_CENTER, TENTH_CENTER))
CONFIRMATION_CENTER = (0., 0., -50.)
CHANNEL_REACH = 12
BEAM_WIDTH = 4
LOOKAHEAD_DEPTH = 3


@dataclass(frozen=True)
class FoldAudit:
    center: tuple[float, float, float]
    candidates: int
    colored_positives: int
    first_exact_band: int | None
    first_band_correct_sites: int
    first_band_false_sites: int


@dataclass(frozen=True)
class ContinuousSectionConfirmation:
    training_centers: tuple[tuple[float, float, float], ...]
    confirmation_center: tuple[float, float, float]
    training_nuclei: int
    training_examples: int
    training_colored_positives: int
    leave_one_nucleus_out: tuple[FoldAudit, ...]
    nuclei_with_exact_action_in_reach: int
    continuous_model_digest: str
    channel_reach: int
    beam_width: int
    lookahead_depth: int
    minimum_center_separation: float
    required_center_separation: float
    spatial_domains_disjoint: bool
    confirmation_seed_atoms: int
    confirmation_target_atoms: int
    frozen_candidate_bands: int
    frozen_candidate_digest: str
    selected_path_ranks: tuple[int, ...]
    first_exact_candidate_rank: int | None
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    target_materialized_after_trace_freeze: bool
    target_used_for_selection: bool
    continuous_spatial_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _colored_truth(proposals, band, target):
    target_colors = {
        tuple(round(value, 6) for value in point): color
        for point, color in zip(target.positions, target.species)}
    correct = sum(
        target_colors.get(tuple(round(value, 6) for value in point)) ==
        _dominant_source_color(proposals, point)
        for point in band)
    return correct, len(band) - correct


def fit_continuous_section(descriptor_version="radial-v1"):
    """Fit one colored, rigid-motion-invariant section on completed nuclei."""
    origin_seed, _ = oracle_patch(3, 9.)
    origin_target, _ = oracle_patch(4, EVALUATION_TARGET_RADIUS)
    prototypes = local_cluster_types(
        origin_seed.positions, origin_seed.species, CLUSTER_EDGES)
    connection = learn_recursive_connection_marking(
        origin_seed.positions, prototypes, origin_target.positions,
        HIDDEN_UNIT, minimum_purity=.5,
        target_colors=origin_target.species)
    seeds = (origin_seed,) + tuple(
        _seed_crop(center) for center in COMPLETED_TRAINING_CENTERS[1:])
    targets = (origin_target,) + tuple(
        _open_target(center) for center in COMPLETED_TRAINING_CENTERS[1:])
    proposals = tuple(_bounded_proposals(
        connection, prototypes, seed, center)
        for seed, center in zip(seeds, COMPLETED_TRAINING_CENTERS))
    examples = tuple(FrontierAttachmentExample(
        proposal, tuple(seed.positions), tuple(seed.species),
        tuple(target.positions), tuple(target.species))
        for proposal, seed, target in zip(proposals, seeds, targets))

    held_scores = []
    fold_markers = []
    for held_index, (proposal, seed) in enumerate(zip(proposals, seeds)):
        marker = fit_frontier_attachment_marker_examples(tuple(
            example for index, example in enumerate(examples)
            if index != held_index),
            descriptor_version=descriptor_version)
        fold_markers.append(marker)
        held_scores.append(score_frontier_attachments(
            marker, proposal, seed.positions, seed.species))
    augmented_examples = []
    for proposal, seed, target, scores in zip(
            proposals, seeds, targets, held_scores):
        known = {tuple(round(value, 6) for value in point)
                 for point in seed.positions}
        novel = sum(tuple(round(value, 6) for value in point) not in known
                    for point in target.positions)
        augmented = _augmented_frontier(
            proposal, scores, seed.positions, seed.species,
            min(len(scores), 2 * novel))
        augmented_examples.append(FrontierAttachmentExample(
            proposal, tuple(augmented[0]), tuple(augmented[1]),
            tuple(target.positions), tuple(target.species)))
    fold_refinements = tuple(fit_frontier_attachment_marker_examples(tuple(
        example for index, example in enumerate(augmented_examples)
        if index != held_index), descriptor_version=descriptor_version)
        for held_index in range(len(examples)))
    marker = fit_frontier_attachment_marker_examples(
        examples, descriptor_version=descriptor_version)
    refinement = fit_frontier_attachment_marker_examples(
        tuple(augmented_examples), descriptor_version=descriptor_version)

    folds = []
    for center, proposal, seed, target, first, second in zip(
            COMPLETED_TRAINING_CENTERS, proposals, seeds, targets,
            fold_markers, fold_refinements):
        scores = score_frontier_attachments(
            first, proposal, seed.positions, seed.species)
        known = {tuple(round(value, 6) for value in point)
                 for point in seed.positions}
        novel = sum(tuple(round(value, 6) for value in point) not in known
                    for point in target.positions)
        augmented = _augmented_frontier(
            proposal, scores, seed.positions, seed.species,
            min(len(scores), 2 * novel))
        refined = score_frontier_attachments(
            second, proposal, *augmented)
        levels = sorted(set(refined.values()), reverse=True)[:CHANNEL_REACH]
        bands = tuple(tuple(sorted(
            point for point, value in refined.items()
            if abs(value - level) <= 1e-12)) for level in levels)
        truth = tuple(_colored_truth(proposal, band, target)
                      for band in bands)
        first_exact = next((rank for rank, (correct, false) in
                            enumerate(truth, 1)
                            if correct and not false), None)
        first_truth = truth[0] if truth else (0, 0)
        target_keys = {tuple(round(value, 6) for value in point): color
                       for point, color in zip(target.positions,
                                               target.species)}
        positives = sum(
            target_keys.get(tuple(round(value, 6) for value in point)) ==
            _dominant_source_color(proposal, point)
            for point in proposal.votes)
        folds.append(FoldAudit(
            tuple(center), len(proposal.votes), positives, first_exact,
            first_truth[0], first_truth[1]))
    return prototypes, connection, seeds, targets, marker, refinement, \
        tuple(folds)


def evaluate() -> ContinuousSectionConfirmation:
    (prototypes, connection, seeds, targets, marker, refinement,
     folds) = fit_continuous_section()
    model_digest = hashlib.sha256(repr((marker, refinement)).encode()).hexdigest()
    minimum = min(math.dist(CONFIRMATION_CENTER, center)
                  for center in COMPLETED_TRAINING_CENTERS)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum > required

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
        CONFIRMATION_CENTER, EVALUATION_TARGET_RADIUS, waves=1,
        beam_width=BEAM_WIDTH, branching_width=CHANNEL_REACH,
        lookahead_depth=LOOKAHEAD_DEPTH, root_rank_values=rank_values,
        candidate_snapshot_width=CHANNEL_REACH)
    frozen_payload = (model_digest, result.records, result.traces,
                      result.decisions)
    frozen_digest = hashlib.sha256(repr(frozen_payload).encode()).hexdigest()

    # First and only construction of the fresh outer target.
    target = _open_target(CONFIRMATION_CENTER)
    scored = score_regenerative_growth(
        result.records, result.traces, seed.positions,
        target.positions, target.species)
    decision = result.decisions[0]
    target_colors = {tuple(round(value, 6) for value in point): color
                     for point, color in zip(target.positions,
                                             target.species)}
    truths = tuple((sum(
        target_colors.get(tuple(round(value, 6) for value in point)) == color
        for point, color in zip(points, colors)), len(points))
        for points, colors in zip(decision.first_candidate_positions,
                                  decision.first_candidate_species))
    first_exact = next((rank for rank, (correct, total) in
                        zip(decision.first_candidate_ranks, truths)
                        if total and correct == total), None)
    correct = sum(row.true_sites for row in scored)
    false = sum(row.false_sites for row in scored)
    emitted = correct + false
    target_used = result.target_used_for_selection
    passed = bool(disjoint and emitted and not false and not target_used and
                  first_exact is not None and
                  decision.selected_path_ranks[0] == first_exact)
    return ContinuousSectionConfirmation(
        COMPLETED_TRAINING_CENTERS, CONFIRMATION_CENTER,
        len(COMPLETED_TRAINING_CENTERS),
        marker.training_examples, marker.training_positives, folds,
        sum(fold.first_exact_band is not None for fold in folds),
        model_digest, CHANNEL_REACH, BEAM_WIDTH, LOOKAHEAD_DEPTH,
        minimum, required, disjoint, len(seed.positions),
        len(target.positions), len(decision.first_candidate_ranks),
        frozen_digest, decision.selected_path_ranks, first_exact,
        emitted, correct, false, correct / emitted if emitted else 0.,
        True, target_used, passed, False,
        ("continuous colored section transfers to a fresh nucleus"
         if passed else
         "continuous colored section remains spatially unconfirmed"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
