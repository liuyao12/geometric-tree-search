#!/usr/bin/env python3
"""Eighth-nucleus test of channel reach learned from exact alternatives.

The predeclared seventh-nucleus invocation lost its result at the execution
transport boundary and is treated as consumed/unknown.  No value or candidate
information from it enters this unchanged-policy retry on a new disjoint ball.
"""

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
from materials_gcts_iqc_rank_value_confirmation import (
    CONFIRMATION_CENTER as SIXTH_CENTER)
from materials_gcts_iqc_robust_persistent_beam_confirmation import (
    CONFIRMATION_CENTER as FIFTH_CENTER)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS)
from materials_gcts_rank_calibrated_value import (
    FrozenRankValue, RankValueObservation, fit_rank_value)


ABORTED_SEVENTH_CENTER = (20., 20., -25.)
CONFIRMATION_CENTER = (-25., 20., -20.)


def _observation(label, correct, false):
    return RankValueObservation(
        hashlib.sha256(label.encode()).hexdigest(), correct, false)


TRAINING_OBSERVATIONS = (
    _observation("fourth", (0, 0, 3, 3), (3, 3, 0, 0)),
    _observation("fifth", (0, 0, 0, 1), (1, 1, 1, 0)),
    _observation("sixth-wave-1",
                 (0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0),
                 (1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1)),
    _observation("sixth-wave-2",
                 (0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1),
                 (1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0)),
)


@dataclass(frozen=True)
class ChannelCountConfirmation:
    model: FrozenRankValue
    exact_training_ranks: tuple[int, ...]
    learned_channel_reach: int
    retained_configuration_width: int
    aborted_seventh_center: tuple[float, float, float]
    aborted_seventh_result_unavailable: bool
    confirmation_center: tuple[float, float, float]
    minimum_center_separation: float
    required_center_separation: float
    all_target_balls_pairwise_disjoint: bool
    policy_frozen_before_confirmation: bool
    result: PersistentBeamDiagnostic
    spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate():
    exact_ranks = tuple(sorted({
        rank for observation in TRAINING_OBSERVATIONS
        for rank, (correct, false) in enumerate(zip(
            observation.correct_sites, observation.false_sites), 1)
        if correct > 0 and false == 0}))
    channel_reach = max(exact_ranks)
    model = fit_rank_value(
        TRAINING_OBSERVATIONS, maximum_rank=channel_reach)
    prior = TRAINING_CENTERS + (
        FOURTH_CENTER, FIFTH_CENTER, SIXTH_CENTER,
        ABORTED_SEVENTH_CENTER)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum > required
    result = evaluate_persistent(
        lookahead_depth=3, beam_width=4, branching_width=channel_reach,
        robust_marking=True, evaluation_center=CONFIRMATION_CENTER,
        root_rank_values=model.as_mapping(), waves=1,
        candidate_snapshot_width=channel_reach)
    passed = (disjoint and result.all_executed_actions_exact and
              not result.target_used_for_selection)
    return ChannelCountConfirmation(
        model, exact_ranks, channel_reach, 4, ABORTED_SEVENTH_CENTER, True,
        CONFIRMATION_CENTER,
        minimum, required, disjoint, True, result, passed, False,
        ("learned IQC channel reach passes eighth-nucleus confirmation"
         if passed else "learned IQC channel reach remains spatially red"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
