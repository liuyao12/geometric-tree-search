#!/usr/bin/env python3
"""Train-only preflight for carried-port IQC antichain lookahead."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    _dominant_source_color)
from materials_gcts_frontier_band_marking import (
    BandTrainingExample, fit_grouped_band_marker, frontier_score_bands)
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_port_state_antichain_confirmation import (
    _refined_scores)
from materials_gcts_iqc_self_fed_section_confirmation import (
    _band_truth, fit_self_fed_section)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS)
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)
from materials_gcts_port_obligation_search import (
    LOOKAHEAD_BAND_FEATURE_NAMES, lookahead_band_features)


MAXIMUM_BANDS = 24
MINIMUM_ACTION_PRECISION = .95
MINIMUM_SELECTED_ACTIONS = 2 * len(COMPLETED_TRAINING_CENTERS)


@dataclass(frozen=True)
class PortObligationPreflight:
    training_centers: tuple[tuple[float, float, float], ...]
    maximum_bands: int
    minimum_action_precision: float
    minimum_selected_actions: int
    seed_actions: int
    seed_positive_actions: int
    seed_model_digest: str
    seed_out_of_fold_logloss: float
    seed_threshold: float
    seed_selected_actions: int
    seed_false_actions: int
    self_fed_actions: int
    self_fed_positive_actions: int
    self_fed_model_digest: str
    self_fed_out_of_fold_logloss: float
    self_fed_threshold: float
    self_fed_selected_actions: int
    self_fed_false_actions: int
    target_or_confirmation_nucleus_accessed: bool
    preflight_passed: bool
    honest_status: str


def _compatible(positions, band):
    minimum = min(math.dist(point, other)
                  for index, point in enumerate(positions)
                  for other in positions[index + 1:])
    return not any(
        math.dist(point, other) < minimum - 1e-8
        for index, point in enumerate(band)
        for other in tuple(positions) + tuple(band[index + 1:]))


def _action_rows(group, center, proposals, positions, colors, target,
                 scores, connection):
    rows = []
    for band in frontier_score_bands(
            proposals, scores, maximum_bands=MAXIMUM_BANDS):
        if not _compatible(positions, band.positions):
            continue
        band_colors = tuple(_dominant_source_color(proposals, point)
                            for point in band.positions)
        _next_positions, _next_colors, future = \
            advance_frontier_configuration(
                connection, proposals, positions, colors,
                band.positions, band_colors, CLUSTER_EDGES, center,
                EVALUATION_TARGET_RADIUS)
        features = lookahead_band_features(
            band.features, proposals, future, connection)
        correct, false = _band_truth(proposals, band.positions, target)
        rows.append(BandTrainingExample(
            group, features, bool(correct and not false),
            len(band.positions)))
    return tuple(rows)


def evaluate():
    (prototypes, connection, seeds, targets, marker, refinement,
     self_marker, self_refinement, _teacher_ranks) = fit_self_fed_section(
         "port-state-v2")
    learned_factor = sum(len(target.positions) / len(seed.positions)
                         for seed, target in zip(seeds, targets)) / len(seeds)
    seed_rows = []
    self_rows = []
    for center, seed, target in zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        pool = min(len(proposals.votes), 2 * max(
            1, round(len(seed.positions) * learned_factor) -
            len(seed.positions)))
        scores = _refined_scores(
            marker, refinement, proposals,
            seed.positions, seed.species, pool)
        seed_rows.extend(_action_rows(
            center, center, proposals, seed.positions, seed.species,
            target, scores, connection))

        chosen = None
        for band in frontier_score_bands(
                proposals, scores, maximum_bands=12):
            correct, false = _band_truth(proposals, band.positions, target)
            if correct and not false and _compatible(
                    seed.positions, band.positions):
                chosen = band
                break
        if chosen is None:
            continue
        chosen_colors = tuple(_dominant_source_color(proposals, point)
                              for point in chosen.positions)
        positions, colors, remaining = advance_frontier_configuration(
            connection, proposals, seed.positions, seed.species,
            chosen.positions, chosen_colors, CLUSTER_EDGES, center,
            EVALUATION_TARGET_RADIUS)
        if not remaining.votes:
            continue
        self_pool = min(len(remaining.votes), 2 * max(
            1, round(len(positions) * learned_factor) - len(positions)))
        self_scores = _refined_scores(
            self_marker, self_refinement, remaining,
            positions, colors, self_pool)
        self_rows.extend(_action_rows(
            center, center, remaining, positions, colors,
            target, self_scores, connection))

    seed_rows = tuple(seed_rows)
    self_rows = tuple(self_rows)
    seed_model, seed_audit = fit_grouped_band_marker(
        seed_rows, ridges=(.1, 1.),
        minimum_precision=MINIMUM_ACTION_PRECISION,
        feature_names=LOOKAHEAD_BAND_FEATURE_NAMES, fit_steps=150)
    self_model, self_audit = fit_grouped_band_marker(
        self_rows, ridges=(.1, 1.),
        minimum_precision=MINIMUM_ACTION_PRECISION,
        feature_names=LOOKAHEAD_BAND_FEATURE_NAMES, fit_steps=150)
    seed_digest = hashlib.sha256(repr(seed_model).encode()).hexdigest()
    self_digest = hashlib.sha256(repr(self_model).encode()).hexdigest()
    passed = bool(
        math.isfinite(seed_audit.threshold) and
        math.isfinite(self_audit.threshold) and
        seed_audit.selected_actions >= MINIMUM_SELECTED_ACTIONS and
        self_audit.selected_actions >= MINIMUM_SELECTED_ACTIONS)
    return PortObligationPreflight(
        COMPLETED_TRAINING_CENTERS, MAXIMUM_BANDS,
        MINIMUM_ACTION_PRECISION, MINIMUM_SELECTED_ACTIONS, len(seed_rows),
        sum(row.successful for row in seed_rows), seed_digest,
        seed_audit.out_of_fold_logloss, seed_audit.threshold,
        seed_audit.selected_actions, seed_audit.selected_false_actions,
        len(self_rows), sum(row.successful for row in self_rows), self_digest,
        self_audit.out_of_fold_logloss, self_audit.threshold,
        self_audit.selected_actions, self_audit.selected_false_actions,
        False, passed,
        ("carried port obligations pass the train-only parallel-action gate"
         if passed else
         "carried port obligations remain below the train-only parallel-action gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
