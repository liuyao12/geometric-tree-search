#!/usr/bin/env python3
"""Confirm whole-band GCTS antichains on a fresh IQC nucleus."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_frontier_attachment_benchmark import (
    IterativeGrowthWave, RegenerativeGrowthTrace, _dominant_source_color,
    score_regenerative_growth)
from materials_gcts_frontier_band_marking import (
    BandTrainingExample, fit_grouped_band_marker, frontier_score_bands,
    score_band)
from materials_gcts_iqc_continuous_section_confirmation import (
    COMPLETED_TRAINING_CENTERS,
    CONFIRMATION_CENTER as FIRST_CONTINUOUS_CENTER)
from materials_gcts_iqc_continuous_section_multistep_confirmation import (
    CONFIRMATION_CENTER as FAILED_MULTISTEP_CENTER)
from materials_gcts_iqc_multinucleus_marking_benchmark import (
    _bounded_proposals)
from materials_gcts_iqc_port_state_antichain_confirmation import (
    CONFIRMATION_CENTER as ABSOLUTE_THRESHOLD_CENTER,
    _refined_scores, _teacher_states)
from materials_gcts_iqc_port_state_section_confirmation import (
    CONFIRMATION_CENTER as PORT_STATE_CENTER)
from materials_gcts_iqc_self_fed_section_confirmation import (
    CONFIRMATION_CENTER as FAILED_SELF_FED_CENTER, _band_truth,
    fit_self_fed_section)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    CLUSTER_EDGES, EVALUATION_TARGET_RADIUS, _open_target, _seed_crop)
from materials_gcts_persistent_frontier_beam import (
    advance_frontier_configuration)


CONFIRMATION_CENTER = (50., 50., 0.)
WAVES = 3
MAXIMUM_BANDS = 24


@dataclass(frozen=True)
class BandAntichainWave:
    wave: int
    candidate_sites: int
    candidate_bands: int
    eligible_bands: int
    accepted_bands: int
    rejected_conflict_bands: int
    emitted_sites: int
    maximum_marking_score: float
    threshold: float


@dataclass(frozen=True)
class BandMarkedAntichainConfirmation:
    training_centers: tuple[tuple[float, float, float], ...]
    confirmation_center: tuple[float, float, float]
    seed_band_model_digest: str
    self_fed_band_model_digest: str
    seed_training_actions: int
    seed_training_positive_actions: int
    self_fed_training_actions: int
    self_fed_training_positive_actions: int
    seed_out_of_fold_logloss: float
    self_fed_out_of_fold_logloss: float
    seed_threshold: float
    self_fed_threshold: float
    seed_threshold_actions: int
    seed_threshold_false_actions: int
    self_fed_threshold_actions: int
    self_fed_threshold_false_actions: int
    requested_waves: int
    executed_waves: int
    minimum_prior_center_separation: float
    required_center_separation: float
    spatial_domains_disjoint: bool
    seed_atoms: int
    target_atoms: int
    wave_audits: tuple[BandAntichainWave, ...]
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


def _training_rows(prototypes, connection, seeds, targets, marker,
                   refinement, learned_factor):
    rows = []
    for center, seed, target in zip(
            COMPLETED_TRAINING_CENTERS, seeds, targets):
        proposals = _bounded_proposals(connection, prototypes, seed, center)
        pool = min(len(proposals.votes), 2 * max(
            1, round(len(seed.positions) * learned_factor) -
            len(seed.positions)))
        scores = _refined_scores(
            marker, refinement, proposals,
            seed.positions, seed.species, pool)
        for band in frontier_score_bands(
                proposals, scores, maximum_bands=MAXIMUM_BANDS):
            correct, false = _band_truth(proposals, band.positions, target)
            rows.append(BandTrainingExample(
                center, band.features, bool(correct and not false),
                len(band.positions)))
    return tuple(rows)


def _self_fed_rows(states, marker, refinement, learned_factor):
    rows = []
    for group, (proposals, positions, colors, target) in enumerate(states):
        pool = min(len(proposals.votes), 2 * max(
            1, round(len(positions) * learned_factor) - len(positions)))
        scores = _refined_scores(
            marker, refinement, proposals, positions, colors, pool)
        for band in frontier_score_bands(
                proposals, scores, maximum_bands=MAXIMUM_BANDS):
            correct, false = _band_truth(proposals, band.positions, target)
            rows.append(BandTrainingExample(
                group, band.features, bool(correct and not false),
                len(band.positions)))
    return tuple(rows)


def _execute(connection, proposals, positions, colors, center, pool,
             markers, refinements, band_markers, thresholds):
    positions, colors = tuple(positions), tuple(colors)
    remaining = proposals
    minimum_separation = min(
        math.dist(point, other)
        for index, point in enumerate(positions)
        for other in positions[index + 1:])
    audits = []
    traces = []
    for wave in range(1, WAVES + 1):
        stage = min(wave - 1, len(markers) - 1)
        scores = _refined_scores(
            markers[stage], refinements[stage], remaining,
            positions, colors, pool)
        bands = frontier_score_bands(
            remaining, scores, maximum_bands=MAXIMUM_BANDS)
        ranked = tuple(sorted([
            (score_band(band_markers[stage], band.features), band)
            for band in bands], key=lambda row: (-row[0], row[1].rank)))
        eligible = tuple(row for row in ranked
                         if row[0] >= thresholds[stage] - 1e-15)
        accepted_positions = []
        accepted_colors = []
        accepted_bands = conflicts = 0
        for _mark, band in eligible:
            band_colors = tuple(_dominant_source_color(remaining, point)
                                for point in band.positions)
            occupied = positions + tuple(accepted_positions)
            conflict = any(
                math.dist(point, other) < minimum_separation - 1e-8
                for index, point in enumerate(band.positions)
                for other in occupied + band.positions[index + 1:])
            if conflict:
                conflicts += 1
                continue
            accepted_bands += 1
            accepted_positions.extend(band.positions)
            accepted_colors.extend(band_colors)
        audit = BandAntichainWave(
            wave, len(scores), len(bands), len(eligible), accepted_bands,
            conflicts, len(accepted_positions),
            max((row[0] for row in ranked), default=0.), thresholds[stage])
        audits.append(audit)
        if not accepted_positions:
            break
        band = tuple(accepted_positions)
        band_colors = tuple(accepted_colors)
        traces.append(RegenerativeGrowthTrace(wave, band, band_colors))
        positions, colors, remaining = advance_frontier_configuration(
            connection, remaining, positions, colors, band, band_colors,
            CLUSTER_EDGES, center, EVALUATION_TARGET_RADIUS)
    return tuple(audits), tuple(traces)


def evaluate():
    (prototypes, connection, seeds, targets, marker, refinement,
     self_marker, self_refinement, _teacher_ranks) = fit_self_fed_section(
         "port-state-v2")
    learned_factor = sum(len(target.positions) / len(seed.positions)
                         for seed, target in zip(seeds, targets)) / len(seeds)
    seed_rows = _training_rows(
        prototypes, connection, seeds, targets, marker, refinement,
        learned_factor)
    teacher = _teacher_states(
        prototypes, connection, seeds, targets, marker, refinement,
        learned_factor)
    self_rows = _self_fed_rows(
        teacher, self_marker, self_refinement, learned_factor)
    seed_band_marker, seed_audit = fit_grouped_band_marker(seed_rows)
    self_band_marker, self_audit = fit_grouped_band_marker(self_rows)
    seed_digest = hashlib.sha256(repr(seed_band_marker).encode()).hexdigest()
    self_digest = hashlib.sha256(repr(self_band_marker).encode()).hexdigest()

    prior = COMPLETED_TRAINING_CENTERS + (
        FIRST_CONTINUOUS_CENTER, FAILED_MULTISTEP_CENTER,
        FAILED_SELF_FED_CENTER, PORT_STATE_CENTER,
        ABSOLUTE_THRESHOLD_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    if not (math.isfinite(seed_audit.threshold) and
            math.isfinite(self_audit.threshold)):
        frozen_digest = hashlib.sha256(repr((
            seed_digest, self_digest, seed_audit, self_audit,
            "calibration-failed-closed")).encode()).hexdigest()
        return BandMarkedAntichainConfirmation(
            COMPLETED_TRAINING_CENTERS, CONFIRMATION_CENTER,
            seed_digest, self_digest, len(seed_rows),
            sum(row.successful for row in seed_rows), len(self_rows),
            sum(row.successful for row in self_rows),
            seed_audit.out_of_fold_logloss, self_audit.out_of_fold_logloss,
            seed_audit.threshold, self_audit.threshold,
            seed_audit.selected_actions, seed_audit.selected_false_actions,
            self_audit.selected_actions, self_audit.selected_false_actions,
            WAVES, 0,
            minimum, required, minimum > required, 0, 0, (), (), (), (),
            0, 0, 0, 0., 0., frozen_digest, False, False, False, False,
            False, "group-heldout band calibration failed closed")

    seed = _seed_crop(CONFIRMATION_CENTER)
    proposals = _bounded_proposals(
        connection, prototypes, seed, CONFIRMATION_CENTER)
    pool = min(len(proposals.votes), 2 * max(
        1, round(len(seed.positions) * learned_factor) - len(seed.positions)))
    audits, traces = _execute(
        connection, proposals, seed.positions, seed.species,
        CONFIRMATION_CENTER, pool, (marker, self_marker),
        (refinement, self_refinement),
        (seed_band_marker, self_band_marker),
        (seed_audit.threshold, self_audit.threshold))
    frozen_digest = hashlib.sha256(repr((
        seed_digest, self_digest, seed_audit, self_audit,
        audits, traces)).encode()).hexdigest()

    # The new target first exists after all antichain decisions freeze.
    target = _open_target(CONFIRMATION_CENTER)
    cumulative = 0
    records = []
    for trace, audit in zip(traces, audits):
        cumulative += len(trace.positions)
        records.append(IterativeGrowthWave(
            trace.wave, len(trace.positions), -1, -1, cumulative,
            float("nan"), float("nan"), audit.maximum_marking_score,
            audit.candidate_sites))
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
    exact = bool(minimum > required and len(traces) == WAVES and
                 emitted and not false)
    amplification = bool(exact and len(ratios) == WAVES - 1 and
                         min(ratios) > 1.)
    return BandMarkedAntichainConfirmation(
        COMPLETED_TRAINING_CENTERS, CONFIRMATION_CENTER,
        seed_digest, self_digest, len(seed_rows),
        sum(row.successful for row in seed_rows), len(self_rows),
        sum(row.successful for row in self_rows),
        seed_audit.out_of_fold_logloss, self_audit.out_of_fold_logloss,
        seed_audit.threshold, self_audit.threshold,
        seed_audit.selected_actions, seed_audit.selected_false_actions,
        self_audit.selected_actions, self_audit.selected_false_actions,
        WAVES, len(traces),
        minimum, required, minimum > required, len(seed.positions),
        len(target.positions), audits, emitted_by_wave, correct_by_wave,
        false_by_wave, emitted, correct, false,
        correct / emitted if emitted else 0., min(ratios, default=0.),
        frozen_digest, True, False, exact, amplification, False,
        ("exact band-marked antichains amplify across three waves"
         if amplification else
         "whole-band antichain growth remains below the amplification gate"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
