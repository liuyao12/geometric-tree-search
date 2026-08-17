#!/usr/bin/env python3
"""One-shot spatial confirmation of the frozen width-five IQC beam."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass

from materials_gcts_iqc_spatial_beam_transfer_benchmark import (
    EVALUATION_TARGET_RADIUS, SpatialBeamTransferBenchmark,
    TRAIN_OUTER_RADIUS, evaluate as evaluate_spatial_beam)


DIAGNOSTIC_CENTER = (30.0, 0.0, 0.0)
CONFIRMATION_CENTER = (18.0, 25.0, 14.0)
FROZEN_BEAM_WIDTH = 5


@dataclass(frozen=True)
class SpatialWidthFiveConfirmation:
    diagnostic_center: tuple[float, float, float]
    confirmation_center: tuple[float, float, float]
    diagnostic_confirmation_separation: float
    summed_evaluation_radii: float
    evaluation_domains_disjoint: bool
    center_squared_norms_differ: bool
    beam_width_frozen_before_confirmation: bool
    result: SpatialBeamTransferBenchmark
    spatial_confirmation_passed: bool
    stationary_or_exponential_certificate: bool
    honest_status: str


def evaluate(waves: int = 1) -> SpatialWidthFiveConfirmation:
    separation = math.dist(DIAGNOSTIC_CENTER, CONFIRMATION_CENTER)
    disjoint = separation > 2.0 * EVALUATION_TARGET_RADIUS
    norm_diagnostic = sum(value * value for value in DIAGNOSTIC_CENTER)
    norm_confirmation = sum(value * value for value in CONFIRMATION_CENTER)
    norms_differ = not math.isclose(norm_diagnostic, norm_confirmation)
    if math.dist((0., 0., 0.), CONFIRMATION_CENTER) <= (
            TRAIN_OUTER_RADIUS + EVALUATION_TARGET_RADIUS):
        raise AssertionError("confirmation target overlaps the training domain")
    result = evaluate_spatial_beam(
        waves, evaluation_center=CONFIRMATION_CENTER,
        beam_width=FROZEN_BEAM_WIDTH)
    passed = (disjoint and norms_differ and
              result.independent_growth_gate_passed)
    return SpatialWidthFiveConfirmation(
        DIAGNOSTIC_CENTER, CONFIRMATION_CENTER, separation,
        2.0 * EVALUATION_TARGET_RADIUS, disjoint, norms_differ, True,
        result, passed, False,
        ("width-five option-preserving IQC search transfers spatially"
         if passed else
         "width-five option-preserving IQC search fails spatial confirmation"))


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
