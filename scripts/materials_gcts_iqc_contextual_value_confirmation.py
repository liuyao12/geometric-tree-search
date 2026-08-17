#!/usr/bin/env python3
"""Ninth-nucleus two-wave confirmation of a carried contextual GCTS value."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_iqc_channel_count_confirmation import (
    ABORTED_SEVENTH_CENTER, CONFIRMATION_CENTER as EIGHTH_CENTER)
from materials_gcts_iqc_multinucleus_marking_benchmark import TRAINING_CENTERS
from materials_gcts_iqc_persistent_beam_diagnostic import (
    CONFIRMATION_CENTER as FOURTH_CENTER, PersistentBeamDiagnostic,
    evaluate as evaluate_persistent)
from materials_gcts_iqc_rank_value_confirmation import (
    CONFIRMATION_CENTER as SIXTH_CENTER)
from materials_gcts_iqc_robust_persistent_beam_confirmation import (
    CONFIRMATION_CENTER as FIFTH_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS)
from materials_gcts_rank_calibrated_value import (
    ContextualRankValueObservation, FrozenContextualRankValue,
    RankValueObservation, fit_contextual_rank_value)


CONFIRMATION_CENTER = (-25., -20., 20.)


def _observation(label, context, correct, false):
    base = RankValueObservation(
        hashlib.sha256(label.encode()).hexdigest(), correct, false)
    return ContextualRankValueObservation(context, base)


CONTEXTUAL_OBSERVATIONS = (
    _observation("fourth-initial", 0, (0, 0, 3, 3), (3, 3, 0, 0)),
    _observation("fifth-initial", 0, (0, 0, 0, 1), (1, 1, 1, 0)),
    _observation("sixth-initial", 0,
                 (0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0),
                 (1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1)),
    _observation("eighth-initial", 0,
                 (0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0),
                 (1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1)),
    _observation("sixth-after-4", 4,
                 (0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1),
                 (1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0)),
    _observation("eighth-after-4", 4,
                 (0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1),
                 (1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0)),
)


@dataclass(frozen=True)
class ContextualValueConfirmation:
    model: FrozenContextualRankValue
    context_zero_values: tuple[float, ...]
    context_after_four_values: tuple[float, ...]
    channel_reach: int
    confirmation_center: tuple[float, float, float]
    minimum_center_separation: float
    required_center_separation: float
    all_target_balls_pairwise_disjoint: bool
    model_frozen_before_confirmation: bool
    result: PersistentBeamDiagnostic
    two_wave_spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate():
    model = fit_contextual_rank_value(
        CONTEXTUAL_OBSERVATIONS, maximum_rank=12)
    mapping = model.as_mapping()
    prior = TRAINING_CENTERS + (
        FOURTH_CENTER, FIFTH_CENTER, SIXTH_CENTER,
        ABORTED_SEVENTH_CENTER, EIGHTH_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum > required
    result = evaluate_persistent(
        lookahead_depth=3, beam_width=4, branching_width=12,
        robust_marking=True, evaluation_center=CONFIRMATION_CENTER,
        root_rank_values=mapping[0],
        root_rank_values_by_previous=mapping, waves=2,
        candidate_snapshot_width=12)
    passed = (disjoint and result.executed_waves == 2 and
              result.all_executed_actions_exact and
              not result.target_used_for_selection)
    return ContextualValueConfirmation(
        model, tuple(mapping[0][rank] for rank in range(1, 13)),
        tuple(mapping[4][rank] for rank in range(1, 13)), 12,
        CONFIRMATION_CENTER, minimum, required, disjoint, True,
        result, passed, False,
        ("contextual GCTS value passes two-wave spatial confirmation"
         if passed else "contextual GCTS value remains spatially red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
