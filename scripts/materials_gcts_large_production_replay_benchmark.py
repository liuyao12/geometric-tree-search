#!/usr/bin/env python3
"""Frozen exact-production recognition on the 155k-site IQC fixture."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_guarded_production_atlas import (
    fit_frozen_production_atlas, replay_frozen_production_atlas)
from materials_gcts_guarded_radial_hierarchy import fit_guarded_radial_hierarchy
from materials_gcts_icosahedral_modelset import HIDDEN_UNIT, oracle_patch_fast


@dataclass(frozen=True)
class LargeProductionReplayBenchmark:
    training_atoms: int
    heldout_atoms: int
    sampled_training_parents: Tuple[int, ...]
    parent_colors: Tuple[int, ...]
    production_alternatives: Tuple[int, ...]
    maximum_alternatives_per_color: Tuple[int, ...]
    sampled_heldout_parents: Tuple[int, ...]
    heldout_known_color_fractions: Tuple[float, ...]
    exact_production_fractions: Tuple[float, ...]
    exact_given_known_color: Tuple[float, ...]
    unseen_production_fingerprints: Tuple[int, ...]
    heldout_geometry_used_for_fitting: bool
    exact_three_level_production_transfer: bool
    production_execution_verified: bool
    benchmark_passed: bool


def evaluate(sample_limit=4096):
    training_radius = 35.0
    heldout_radius = 9.0 * HIDDEN_UNIT ** 4
    training, _ = oracle_patch_fast(11, training_radius)
    heldout, _ = oracle_patch_fast(19, heldout_radius)
    encoder = fit_guarded_radial_hierarchy(training, training_radius)
    atlas = fit_frozen_production_atlas(
        training, encoder, sample_limit_per_level=sample_limit)
    replay = replay_frozen_production_atlas(
        heldout, encoder, atlas, heldout_radius)
    exact = min(item.exact_production_fraction for item in replay) >= .90
    # Recognition does not recover a proper pose from incoming ports.
    execution = False
    return LargeProductionReplayBenchmark(
        len(training.positions), len(heldout.positions),
        tuple(item.sampled_training_parents for item in atlas.levels),
        tuple(item.parent_colors for item in atlas.levels),
        tuple(item.production_alternatives for item in atlas.levels),
        tuple(item.maximum_alternatives_per_color for item in atlas.levels),
        tuple(item.sampled_heldout_parents for item in replay),
        tuple(item.known_color_fraction for item in replay),
        tuple(item.exact_production_fraction for item in replay),
        tuple(item.exact_given_known_color for item in replay),
        tuple(item.unseen_production_fingerprints for item in replay),
        atlas.geometry_uses_heldout_atoms, exact, execution,
        exact and execution)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=4096)
    arguments = parser.parse_args()
    result = evaluate(arguments.sample_limit)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
