#!/usr/bin/env python3
"""Sixth-nucleus confirmation of a train-calibrated IQC branch value."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_iqc_multinucleus_marking_benchmark import TRAINING_CENTERS
from materials_gcts_iqc_persistent_beam_diagnostic import (
    CONFIRMATION_CENTER as FOURTH_CENTER, PersistentBeamDiagnostic,
    evaluate as evaluate_persistent)
from materials_gcts_iqc_robust_persistent_beam_confirmation import (
    CONFIRMATION_CENTER as FIFTH_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS)
from materials_gcts_rank_calibrated_value import (
    FrozenRankValue, RankValueObservation, fit_rank_value)


CONFIRMATION_CENTER = (-20., -20., -25.)


def _training_observation(center, correct, false):
    digest = hashlib.sha256(repr((center, correct, false)).encode()).hexdigest()
    return RankValueObservation(digest, correct, false)


TRAINING_OBSERVATIONS = (
    _training_observation(
        FOURTH_CENTER, (0, 0, 3, 3), (3, 3, 0, 0)),
    _training_observation(
        FIFTH_CENTER, (0, 0, 0, 1), (1, 1, 1, 0)),
)


@dataclass(frozen=True)
class RankValueConfirmation:
    model: FrozenRankValue
    confirmation_center: tuple[float, float, float]
    minimum_center_separation: float
    required_center_separation: float
    all_target_balls_pairwise_disjoint: bool
    model_frozen_before_confirmation: bool
    result: PersistentBeamDiagnostic
    spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate() -> RankValueConfirmation:
    model = fit_rank_value(TRAINING_OBSERVATIONS)
    prior = TRAINING_CENTERS + (FOURTH_CENTER, FIFTH_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum > required
    result = evaluate_persistent(
        lookahead_depth=3, beam_width=4, branching_width=4,
        robust_marking=True, evaluation_center=CONFIRMATION_CENTER,
        root_rank_values=model.as_mapping())
    passed = (disjoint and result.exact_first_action_recovered and
              not result.target_used_for_selection)
    return RankValueConfirmation(
        model, CONFIRMATION_CENTER, minimum, required, disjoint, True,
        result, passed, False,
        ("learned IQC branch value passes sixth-nucleus confirmation"
         if passed else "learned IQC branch value remains spatially red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
