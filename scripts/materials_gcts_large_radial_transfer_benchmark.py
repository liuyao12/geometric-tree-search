#!/usr/bin/env python3
"""Large cumulative-guard IQC transfer benchmark using the fast oracle."""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_guarded_radial_hierarchy import (
    fit_guarded_radial_hierarchy, replay_guarded_radial_hierarchy)
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch_fast
from materials_gcts_generic import AtomicConfiguration
from materials_pointset_benchmarks import amorphous_hard_core_point_set


@dataclass(frozen=True)
class LargeRadialTransferBenchmark:
    training_atoms: int
    heldout_oracle_atoms: int
    training_radius: float
    heldout_radius: float
    oracle_generation_seconds: float
    training_centers: Tuple[int, ...]
    heldout_centers: Tuple[int, ...]
    dependency_radii: Tuple[float, ...]
    frozen_signatures: Tuple[int, ...]
    promoted_signatures: Tuple[int, ...]
    heldout_known_fractions: Tuple[float, ...]
    heldout_promoted_fractions: Tuple[float, ...]
    median_nearest_color_distances: Tuple[float, ...]
    p95_nearest_color_distances: Tuple[float, ...]
    amorphous_centers: Tuple[int, ...]
    amorphous_promoted_fractions: Tuple[float, ...]
    maximum_amorphous_promoted_fraction: float
    amorphous_rejected_at_first_and_third_level: bool
    all_raw_domains_disjoint: bool
    three_nonempty_levels: bool
    minimum_known_fraction: float
    minimum_promoted_fraction: float
    benchmark_passed: bool


def evaluate():
    # Maximize training evidence while leaving two cumulative level-three
    # dependency radii between the fit and held-out shells.
    training_radius = 35.0
    heldout_radius = 9.0 * HIDDEN_UNIT ** 4
    training, _ = oracle_patch_fast(11, training_radius)
    started = time.perf_counter()
    heldout, _ = oracle_patch_fast(19, heldout_radius)
    oracle_seconds = time.perf_counter() - started
    encoder = fit_guarded_radial_hierarchy(training, training_radius)
    reports = replay_guarded_radial_hierarchy(
        heldout, encoder, heldout_radius)
    null = amorphous_hard_core_point_set(
        atom_count=3000, radius=16.5, min_distance=.72, seed=817)
    null_positions = tuple((point[0] + 44.0, point[1], point[2])
                           for point in null.positions)
    rng = random.Random(4)
    null_species = tuple(rng.choices(
        ("X", "Y", "Z"), (.25, .5, .25), k=len(null_positions)))
    null_reports = replay_guarded_radial_hierarchy(
        AtomicConfiguration(null.name, null_positions, null_species),
        encoder, heldout_radius)
    nonempty = len(reports) == 3 and min(
        item.heldout_centers for item in reports) >= 100
    minimum_known = min(item.known_heldout_fraction for item in reports)
    minimum_promoted = min(item.promoted_heldout_fraction for item in reports)
    disjoint = all(item.raw_domains_disjoint for item in reports)
    null_fractions = tuple(item.promoted_heldout_fraction
                           for item in null_reports)
    null_rejected = null_fractions[0] < .5 and null_fractions[2] < .5
    passed = (nonempty and disjoint and minimum_promoted >= .95 and
              null_rejected)
    return LargeRadialTransferBenchmark(
        len(training.positions), len(heldout.positions), training_radius,
        heldout_radius, oracle_seconds,
        tuple(item.training_centers for item in reports),
        tuple(item.heldout_centers for item in reports),
        tuple(item.dependency_radius for item in reports),
        tuple(item.frozen_signatures for item in reports),
        tuple(item.promoted_signatures for item in reports),
        tuple(item.known_heldout_fraction for item in reports),
        tuple(item.promoted_heldout_fraction for item in reports),
        tuple(item.median_nearest_color_distance for item in reports),
        tuple(item.p95_nearest_color_distance for item in reports),
        tuple(item.heldout_centers for item in null_reports), null_fractions,
        max(null_fractions), null_rejected,
        disjoint, nonempty, minimum_known, minimum_promoted, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
