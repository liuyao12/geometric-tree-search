#!/usr/bin/env python3
"""Fit one local GCTS attachment marking on three nuclei, test a fourth."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment import (
    FrontierAttachmentEnsemble, FrontierAttachmentExample,
    fit_frontier_attachment_marker_examples, score_frontier_attachments)
from materials_gcts_frontier_attachment_benchmark import (
    _augmented_frontier, _dominant_source_color,
    _regenerative_maximum_plateaus, _subset_proposals,
    _without_known_sites, score_regenerative_growth)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_SEED_RADIUS, EVALUATION_TARGET_RADIUS,
    _open_target, _seed_crop)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch
from materials_gcts_recursive_connections import (
    learn_recursive_connection_marking, local_cluster_types,
    map_to_prototypes, propose_with_recursive_marking)


TRAINING_CENTERS = ((0., 0., 0.), (30., 0., 0.), (18., 25., 14.))
CONFIRMATION_CENTER = (-20., 20., 20.)
FROZEN_BEAM_WIDTH = 4


@dataclass(frozen=True)
class MultiNucleusMarkingBenchmark:
    training_centers: tuple[tuple[float, float, float], ...]
    confirmation_center: tuple[float, float, float]
    training_seed_atoms: tuple[int, ...]
    training_target_atoms: tuple[int, ...]
    training_examples: int
    training_positives: int
    all_target_balls_pairwise_disjoint: bool
    beam_width: int
    confirmation_seed_atoms: int
    confirmation_target_atoms: int
    frozen_candidates: int
    candidate_digest: str
    selected_ranks: tuple[int, ...]
    candidate_true_sites: tuple[int, ...]
    candidate_false_sites: tuple[int, ...]
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    target_materialized_after_execution: bool
    target_used_for_selection: bool
    raw_execution_truth_fields_unavailable: bool
    spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _bounded_proposals(connection, prototypes, seed, center):
    types = local_cluster_types(seed.positions, seed.species, CLUSTER_EDGES)
    proposals = propose_with_recursive_marking(
        connection, seed.positions, map_to_prototypes(types, prototypes),
        HIDDEN_UNIT)
    proposals = _without_known_sites(proposals, seed.positions)
    return _subset_proposals(proposals, (
        point for point in proposals.votes
        if math.dist(point, center) <= EVALUATION_TARGET_RADIUS + 1e-8))


def _pairwise_disjoint(centers):
    return all(math.dist(left, right) > 2. * EVALUATION_TARGET_RADIUS
               for index, left in enumerate(centers)
               for right in centers[index + 1:])


def fit_multinucleus_marking():
    """Fit only from the three completed training nuclei."""
    origin_seed, _ = oracle_patch(3, EVALUATION_SEED_RADIUS)
    origin_target, _ = oracle_patch(4, EVALUATION_TARGET_RADIUS)
    prototypes = local_cluster_types(
        origin_seed.positions, origin_seed.species, CLUSTER_EDGES)
    connection = learn_recursive_connection_marking(
        origin_seed.positions, prototypes, origin_target.positions,
        HIDDEN_UNIT, minimum_purity=.5, target_colors=origin_target.species)

    seeds = (origin_seed,) + tuple(_seed_crop(center)
                                   for center in TRAINING_CENTERS[1:])
    targets = (origin_target,) + tuple(_open_target(center)
                                       for center in TRAINING_CENTERS[1:])
    proposals = tuple(_bounded_proposals(
        connection, prototypes, seed, center)
        for seed, center in zip(seeds, TRAINING_CENTERS))
    examples = tuple(FrontierAttachmentExample(
        proposal, tuple(seed.positions), tuple(seed.species),
        tuple(target.positions))
        for proposal, seed, target in zip(proposals, seeds, targets))
    marker = fit_frontier_attachment_marker_examples(examples)

    held_scores = []
    fold_markers = []
    for held_index, (proposal, seed) in enumerate(zip(proposals, seeds)):
        fold_marker = fit_frontier_attachment_marker_examples(tuple(
            example for index, example in enumerate(examples)
            if index != held_index))
        fold_markers.append(fold_marker)
        held_scores.append(score_frontier_attachments(
            fold_marker, proposal, seed.positions, seed.species))
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
            tuple(target.positions)))
    refinement = fit_frontier_attachment_marker_examples(
        tuple(augmented_examples))
    fold_refinements = tuple(fit_frontier_attachment_marker_examples(tuple(
        example for index, example in enumerate(augmented_examples)
        if index != held_index)) for held_index in range(len(examples)))
    return (prototypes, connection, seeds, targets, proposals, marker,
            refinement, FrontierAttachmentEnsemble(tuple(fold_markers)),
            FrontierAttachmentEnsemble(fold_refinements))


def evaluate(waves: int = 1) -> MultiNucleusMarkingBenchmark:
    if waves < 1:
        raise ValueError("waves must be positive")
    (prototypes, connection, seeds, targets, _training_proposals, marker,
     refinement, _robust_marker,
     _robust_refinement) = fit_multinucleus_marking()

    seed = _seed_crop(CONFIRMATION_CENTER)
    proposal = _bounded_proposals(
        connection, prototypes, seed, CONFIRMATION_CENTER)
    scores = score_frontier_attachments(
        marker, proposal, seed.positions, seed.species)
    learned_factor = sum(len(target.positions) / len(seed_.positions)
                         for seed_, target in zip(seeds, targets)) / len(seeds)
    predicted_novel = max(1, round(len(seed.positions) * learned_factor) -
                          len(seed.positions))
    pool = min(len(scores), 2 * predicted_novel)
    candidate_payload = tuple(sorted(
        (point, _dominant_source_color(proposal, point), scores[point])
        for point in proposal.votes))
    candidate_digest = hashlib.sha256(
        repr(candidate_payload).encode()).hexdigest()
    records, traces, diagnostics, decisions = _regenerative_maximum_plateaus(
        marker, refinement, connection, proposal,
        seed.positions, seed.species, CLUSTER_EDGES, None, pool,
        CONFIRMATION_CENTER, EVALUATION_TARGET_RADIUS, waves=waves,
        beam_start_wave=1, beam_width=FROZEN_BEAM_WIDTH,
        diagnostic_waves=(), beam_objective="frontier-supply")
    if diagnostics:
        raise AssertionError("target-free execution produced diagnostics")
    frozen_trace = hashlib.sha256(repr((traces, decisions)).encode()).hexdigest()

    # First construction of the fourth nucleus' outer target.
    target = _open_target(CONFIRMATION_CENTER)
    scored = score_regenerative_growth(
        records, traces, seed.positions, target.positions, target.species)
    target_colors = {
        tuple(round(value, 6) for value in point): species
        for point, species in zip(target.positions, target.species)}
    first = decisions[0]
    candidate_true = tuple(sum(
        target_colors.get(tuple(round(value, 6) for value in point)) == species
        for point, species in zip(points, colors))
        for points, colors in zip(first.candidate_positions,
                                  first.candidate_species))
    candidate_false = tuple(total - correct for total, correct in zip(
        first.candidate_sites, candidate_true))
    correct = sum(row.true_sites for row in scored)
    false = sum(row.false_sites for row in scored)
    emitted = correct + false
    raw_unscored = all(row.true_sites == row.false_sites == -1
                       for row in records) and all(
        row.selected_true_sites == row.selected_false_sites == -1 and
        not row.candidate_true_sites and not row.candidate_false_sites
        for row in decisions)
    target_used = any(row.target_used_for_selection for row in decisions)
    centers = TRAINING_CENTERS + (CONFIRMATION_CENTER,)
    disjoint = _pairwise_disjoint(centers)
    passed = (disjoint and len(scored) >= 3 and emitted > 0 and false == 0 and
              raw_unscored and not target_used)
    return MultiNucleusMarkingBenchmark(
        TRAINING_CENTERS, CONFIRMATION_CENTER,
        tuple(len(item.positions) for item in seeds),
        tuple(len(item.positions) for item in targets),
        marker.training_examples, marker.training_positives, disjoint,
        FROZEN_BEAM_WIDTH, len(seed.positions), len(target.positions),
        len(proposal.votes), hashlib.sha256(
            (candidate_digest + frozen_trace).encode()).hexdigest(),
        tuple(row.selected_rank for row in decisions), candidate_true,
        candidate_false, emitted, correct, false,
        correct / emitted if emitted else 0., True, target_used, raw_unscored,
        passed, False,
        ("multi-nucleus local marking transfers spatially"
         if passed else "multi-nucleus local marking remains spatially red"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--waves", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate(arguments.waves)
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if arguments.json else result)


if __name__ == "__main__":
    main()
