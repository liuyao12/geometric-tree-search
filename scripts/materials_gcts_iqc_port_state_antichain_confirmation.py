#!/usr/bin/env python3
"""Train-calibrated multi-action IQC growth with continuous port sections."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment import score_frontier_attachments
from materials_gcts_frontier_attachment_benchmark import (
    IterativeGrowthWave, RegenerativeGrowthTrace, _augmented_frontier,
    _dominant_source_color, score_regenerative_growth)
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_port_state_section_confirmation import (
    CONFIRMATION_CENTER as PRIOR_PORT_STATE_CENTER)
from materials_gcts_iqc_self_fed_section_confirmation import (
    _band_truth, fit_self_fed_section)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_iqc_continuous_section_confirmation import (
    CONFIRMATION_CENTER as FIRST_CONTINUOUS_CENTER)
from materials_gcts_iqc_continuous_section_multistep_confirmation import (
    CONFIRMATION_CENTER as FAILED_MULTISTEP_CENTER)
from materials_gcts_iqc_self_fed_section_confirmation import (
    CONFIRMATION_CENTER as FAILED_SELF_FED_CENTER)
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)


CONFIRMATION_CENTER = (0., 0., 50.)
WAVES = 3


@dataclass(frozen=True)
class ThresholdAudit:
    threshold: float
    accepted: int
    correct: int
    false: int
    candidate_rows: int


@dataclass(frozen=True)
class AntichainWave:
    wave: int
    candidates: int
    candidate_bands: int
    eligible_bands: int
    accepted_bands: int
    rejected_conflict_bands: int
    emitted_sites: int
    threshold: float


@dataclass(frozen=True)
class PortStateAntichainConfirmation:
    training_centers: tuple[tuple[float, float, float], ...]
    confirmation_center: tuple[float, float, float]
    base_model_digest: str
    self_fed_model_digest: str
    seed_threshold: ThresholdAudit
    self_fed_threshold: ThresholdAudit
    requested_waves: int
    executed_waves: int
    minimum_prior_center_separation: float
    required_center_separation: float
    spatial_domains_disjoint: bool
    seed_atoms: int
    target_atoms: int
    waves: tuple[AntichainWave, ...]
    emitted_sites_by_wave: tuple[int, ...]
    correct_sites_by_wave: tuple[int, ...]
    false_sites_by_wave: tuple[int, ...]
    emitted_sites: int
    correct_sites: int
    false_sites: int
    precision: float
    minimum_wave_amplification: float
    frozen_execution_digest: str
    target_materialized_after_execution: bool
    target_used_for_selection: bool
    exact_three_wave_gate_passed: bool
    amplification_gate_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def _refined_scores(marker, refinement, proposals, positions, colors, pool):
    scores = score_frontier_attachments(
        marker, proposals, positions, colors)
    augmented = _augmented_frontier(
        proposals, scores, positions, colors, min(pool, len(scores)))
    return score_frontier_attachments(
        refinement, proposals, *augmented)


def _exact_labels(proposals, target):
    target_colors = {tuple(round(value, 6) for value in point): color
                     for point, color in zip(target.positions,
                                             target.species)}
    return {point: target_colors.get(
        tuple(round(value, 6) for value in point)) ==
        _dominant_source_color(proposals, point)
        for point in proposals.votes}


def _calibrate(rows):
    if not rows:
        raise ValueError("threshold calibration needs candidate rows")
    values = sorted({score for score, _label in rows}, reverse=True)
    feasible = []
    for threshold in values:
        selected = tuple(label for score, label in rows
                         if score >= threshold - 1e-15)
        correct = sum(selected)
        false = len(selected) - correct
        if correct and not false:
            feasible.append((correct, threshold, len(selected)))
    if not feasible:
        return ThresholdAudit(float("inf"), 0, 0, 0, len(rows))
    correct, threshold, accepted = max(feasible)
    return ThresholdAudit(threshold, accepted, correct, 0, len(rows))


def _teacher_states(prototypes, connection, seeds, targets, marker,
                    refinement, learned_factor):
    states = []
    for center, seed, target in zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        pool = min(len(proposals.votes), 2 * max(
            1, round(len(seed.positions) * learned_factor) -
            len(seed.positions)))
        scores = _refined_scores(
            marker, refinement, proposals, seed.positions, seed.species, pool)
        levels = sorted(set(scores.values()), reverse=True)[:12]
        chosen = None
        for level in levels:
            band = tuple(sorted(point for point, value in scores.items()
                                if abs(value - level) <= 1e-12))
            correct, false = _band_truth(proposals, band, target)
            if correct and not false:
                chosen = band
                break
        if chosen is None:
            continue
        band_colors = tuple(_dominant_source_color(proposals, point)
                            for point in chosen)
        positions, colors, remaining = advance_frontier_configuration(
            connection, proposals, seed.positions, seed.species,
            chosen, band_colors, CLUSTER_EDGES, center,
            EVALUATION_TARGET_RADIUS)
        if remaining.votes:
            states.append((remaining, positions, colors, target))
    return tuple(states)


def _execute_antichains(connection, proposals, positions, colors, center,
                        pool, marker, refinement, self_marker,
                        self_refinement, seed_threshold, self_threshold):
    positions, colors = tuple(positions), tuple(colors)
    remaining = proposals
    minimum_separation = min(
        math.dist(point, other)
        for index, point in enumerate(positions)
        for other in positions[index + 1:])
    waves = []
    traces = []
    for wave in range(1, WAVES + 1):
        active_marker = marker if wave == 1 else self_marker
        active_refinement = refinement if wave == 1 else self_refinement
        threshold = seed_threshold.threshold if wave == 1 \
            else self_threshold.threshold
        scores = _refined_scores(
            active_marker, active_refinement, remaining,
            positions, colors, pool)
        levels = sorted(set(scores.values()), reverse=True)
        eligible = tuple(level for level in levels
                         if level >= threshold - 1e-15)
        accepted_positions = []
        accepted_colors = []
        accepted_bands = rejected = 0
        for level in eligible:
            band = tuple(sorted(point for point, value in scores.items()
                                if abs(value - level) <= 1e-12))
            band_colors = tuple(_dominant_source_color(remaining, point)
                                for point in band)
            occupied = positions + tuple(accepted_positions)
            conflict = any(
                math.dist(point, other) < minimum_separation - 1e-8
                for index, point in enumerate(band)
                for other in occupied + band[index + 1:])
            if conflict:
                rejected += 1
                continue
            accepted_bands += 1
            accepted_positions.extend(band)
            accepted_colors.extend(band_colors)
        if not accepted_positions:
            break
        band = tuple(accepted_positions)
        band_colors = tuple(accepted_colors)
        waves.append(AntichainWave(
            wave, len(scores), len(levels), len(eligible), accepted_bands,
            rejected, len(band), threshold))
        traces.append(RegenerativeGrowthTrace(wave, band, band_colors))
        positions, colors, remaining = advance_frontier_configuration(
            connection, remaining, positions, colors, band, band_colors,
            CLUSTER_EDGES, center, EVALUATION_TARGET_RADIUS)
    return tuple(waves), tuple(traces)


def evaluate():
    (prototypes, connection, seeds, targets, marker, refinement,
     self_marker, self_refinement, _teacher_ranks) = fit_self_fed_section(
         "port-state-v2")
    base_digest = hashlib.sha256(
        repr((marker, refinement)).encode()).hexdigest()
    self_digest = hashlib.sha256(
        repr((self_marker, self_refinement)).encode()).hexdigest()
    learned_factor = sum(len(target.positions) / len(seed.positions)
                         for seed, target in zip(seeds, targets)) / len(seeds)
    seed_rows = []
    for center, seed, target in zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        pool = min(len(proposals.votes), 2 * max(
            1, round(len(seed.positions) * learned_factor) -
            len(seed.positions)))
        scores = _refined_scores(
            marker, refinement, proposals, seed.positions, seed.species, pool)
        labels = _exact_labels(proposals, target)
        seed_rows.extend((score, labels[point])
                         for point, score in scores.items())
    teacher = _teacher_states(
        prototypes, connection, seeds, targets, marker, refinement,
        learned_factor)
    self_rows = []
    for proposals, positions, colors, target in teacher:
        pool = min(len(proposals.votes), 2 * max(
            1, round(len(positions) * learned_factor) - len(positions)))
        scores = _refined_scores(
            self_marker, self_refinement, proposals, positions, colors, pool)
        labels = _exact_labels(proposals, target)
        self_rows.extend((score, labels[point])
                         for point, score in scores.items())
    seed_threshold = _calibrate(tuple(seed_rows))
    self_threshold = _calibrate(tuple(self_rows))

    seed = _seed_crop(CONFIRMATION_CENTER)
    proposals = _bounded_proposals(
        connection, prototypes, seed, CONFIRMATION_CENTER)
    pool = min(len(proposals.votes), 2 * max(
        1, round(len(seed.positions) * learned_factor) - len(seed.positions)))
    waves, traces = _execute_antichains(
        connection, proposals, seed.positions, seed.species,
        CONFIRMATION_CENTER, pool, marker, refinement, self_marker,
        self_refinement, seed_threshold, self_threshold)
    frozen_digest = hashlib.sha256(repr((
        base_digest, self_digest, seed_threshold, self_threshold,
        waves, traces)).encode()).hexdigest()

    # The new target first exists after all three antichains freeze.
    target = _open_target(CONFIRMATION_CENTER)
    cumulative = 0
    records = []
    for wave in waves:
        cumulative += wave.emitted_sites
        records.append(IterativeGrowthWave(
            wave.wave, wave.emitted_sites, -1, -1, cumulative,
            float("nan"), float("nan"), wave.threshold,
            wave.candidates))
    scored = score_regenerative_growth(
        tuple(records), traces, seed.positions,
        target.positions, target.species)
    correct_by_wave = tuple(row.true_sites for row in scored)
    false_by_wave = tuple(row.false_sites for row in scored)
    emitted_by_wave = tuple(a + b for a, b in zip(
        correct_by_wave, false_by_wave))
    correct, false = sum(correct_by_wave), sum(false_by_wave)
    emitted = correct + false
    ratios = tuple(right / left for left, right in zip(
        emitted_by_wave, emitted_by_wave[1:]) if left)
    prior = COMPLETED_TRAINING_CENTERS + (
        FIRST_CONTINUOUS_CENTER, FAILED_MULTISTEP_CENTER,
        FAILED_SELF_FED_CENTER, PRIOR_PORT_STATE_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    exact_gate = bool(
        minimum > required and len(waves) == WAVES and emitted and not false)
    amplification = bool(exact_gate and ratios and min(ratios) > 1.)
    return PortStateAntichainConfirmation(
        COMPLETED_TRAINING_CENTERS, CONFIRMATION_CENTER,
        base_digest, self_digest, seed_threshold, self_threshold,
        WAVES, len(waves), minimum, required, minimum > required,
        len(seed.positions), len(target.positions), waves,
        emitted_by_wave, correct_by_wave, false_by_wave,
        emitted, correct, false, correct / emitted if emitted else 0.,
        min(ratios, default=0.), frozen_digest, True, False,
        exact_gate, amplification, False,
        ("exact port-state antichains amplify across three waves"
         if amplification else
         "port-state antichain amplification remains red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
