#!/usr/bin/env python3
"""Fifth-nucleus confirmation of the frozen robust persistent IQC beam."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_iqc_multinucleus_marking_benchmark import TRAINING_CENTERS
from materials_gcts_iqc_persistent_beam_diagnostic import (
    CONFIRMATION_CENTER as DIAGNOSTIC_CENTER, PersistentBeamDiagnostic,
    evaluate as evaluate_persistent)
from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS)


CONFIRMATION_CENTER = (20., -25., 20.)
FROZEN_LOOKAHEAD_DEPTH = 3
FROZEN_BEAM_WIDTH = 4
FROZEN_BRANCHING_WIDTH = 4


@dataclass(frozen=True)
class RobustPersistentBeamConfirmation:
    training_centers: tuple[tuple[float, float, float], ...]
    diagnostic_center: tuple[float, float, float]
    confirmation_center: tuple[float, float, float]
    minimum_center_separation: float
    required_center_separation: float
    all_target_balls_pairwise_disjoint: bool
    policy_frozen_before_confirmation: bool
    result: PersistentBeamDiagnostic
    spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate() -> RobustPersistentBeamConfirmation:
    prior = TRAINING_CENTERS + (DIAGNOSTIC_CENTER,)
    minimum = min(math.dist(CONFIRMATION_CENTER, center) for center in prior)
    required = 2. * EVALUATION_TARGET_RADIUS
    disjoint = minimum > required
    result = evaluate_persistent(
        lookahead_depth=FROZEN_LOOKAHEAD_DEPTH,
        beam_width=FROZEN_BEAM_WIDTH,
        branching_width=FROZEN_BRANCHING_WIDTH,
        robust_marking=True, evaluation_center=CONFIRMATION_CENTER)
    passed = (disjoint and result.exact_first_action_recovered and
              not result.target_used_for_selection)
    return RobustPersistentBeamConfirmation(
        TRAINING_CENTERS, DIAGNOSTIC_CENTER, CONFIRMATION_CENTER,
        minimum, required, disjoint, True, result, passed, False,
        ("robust persistent IQC beam passes fifth-nucleus confirmation"
         if passed else
         "robust persistent IQC beam remains red on fifth nucleus"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2, sort_keys=True)
          if args.json else result)


if __name__ == "__main__":
    main()
