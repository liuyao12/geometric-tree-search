#!/usr/bin/env python3
"""Tenth-nucleus three-wave confirmation of carried GCTS channel states."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_iqc_channel_count_confirmation import (
    ABORTED_SEVENTH_CENTER, CONFIRMATION_CENTER as EIGHTH_CENTER)
from materials_gcts_iqc_contextual_value_confirmation import (
    CONFIRMATION_CENTER as NINTH_CENTER, CONTEXTUAL_OBSERVATIONS)
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


CONFIRMATION_CENTER = (30., -25., -20.)
AFTER_TWELVE_TRUTH = (0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0)
AFTER_TWELVE_FALSE = (1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1)


def _after_twelve(label):
    observation = RankValueObservation(
        hashlib.sha256(label.encode()).hexdigest(),
        AFTER_TWELVE_TRUTH, AFTER_TWELVE_FALSE)
    return ContextualRankValueObservation(12, observation)


THREE_CONTEXT_OBSERVATIONS = CONTEXTUAL_OBSERVATIONS + (
    _after_twelve("sixth-after-4-12"),
    _after_twelve("eighth-after-4-12"),
    _after_twelve("ninth-after-4-12"),
)


@dataclass(frozen=True)
class ThreeContextConfirmation:
    model: FrozenContextualRankValue
    contexts: tuple[int, ...]
    context_after_twelve_values: tuple[float, ...]
    independent_after_twelve_observations: int
    confirmation_center: tuple[float, float, float]
    minimum_center_separation: float
    required_center_separation: float
    all_target_balls_pairwise_disjoint: bool
    model_frozen_before_confirmation: bool
    result: PersistentBeamDiagnostic
    three_wave_spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate():
    model = fit_contextual_rank_value(
        THREE_CONTEXT_OBSERVATIONS, maximum_rank=12)
    mapping = model.as_mapping()
    prior = TRAINING_CENTERS + (
        FOURTH_CENTER, FIFTH_CENTER, SIXTH_CENTER,
        ABORTED_SEVENTH_CENTER, EIGHTH_CENTER, NINTH_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum > required
    result = evaluate_persistent(
        lookahead_depth=3, beam_width=4, branching_width=12,
        robust_marking=True, evaluation_center=CONFIRMATION_CENTER,
        root_rank_values=mapping[0],
        root_rank_values_by_previous=mapping, waves=3,
        candidate_snapshot_width=12)
    passed = (disjoint and result.executed_waves == 3 and
              result.all_executed_actions_exact and
              not result.target_used_for_selection)
    return ThreeContextConfirmation(
        model, model.contexts,
        tuple(mapping[12][rank] for rank in range(1, 13)), 3,
        CONFIRMATION_CENTER, minimum, required, disjoint, True,
        result, passed, False,
        ("three-context GCTS passes three-wave spatial confirmation"
         if passed else "three-context GCTS remains spatially red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
