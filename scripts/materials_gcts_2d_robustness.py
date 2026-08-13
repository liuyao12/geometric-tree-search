#!/usr/bin/env python3
"""Noise and missing-atom gates for the generic planar GCTS atlas."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Dict, Optional, Sequence, Tuple

from materials_gcts_2d_generic_atlas import (
    GenericPlanarAtlas, Vector, grow, layered_hexagonal_configuration,
    learn_planar_atlas)
from materials_gcts_generic import AtomicConfiguration


@dataclass(frozen=True)
class PlanarRobustnessCase:
    system: str
    clean_seed_atoms: int
    observed_seed_atoms: int
    heldout_atoms: int
    coordinate_noise_sigma: float
    missing_seed_fraction: float
    learned_components: int
    learned_motif_atoms: Tuple[int, ...]
    minimum_translation_support: float
    registered_position_precision: float
    registered_position_recall: float
    registered_chemical_accuracy: float
    registered_rms_error: float
    pose_marking_ablation_recall: float
    marking_recall_gain: float
    target_atoms_used_for_learning: bool
    physical_potential_used: bool


def corrupt_seed(configuration: AtomicConfiguration, sigma: float,
                 missing_fraction: float, seed: int) -> AtomicConfiguration:
    rng = random.Random(seed)
    keep = [index for index in range(len(configuration.positions))
            if rng.random() >= missing_fraction]
    positions = tuple(tuple(configuration.positions[index][axis] +
                            rng.gauss(0.0, sigma) for axis in range(3))
                      for index in keep)
    return AtomicConfiguration(
        configuration.name + "-corrupted", positions,
        tuple(configuration.species[index] for index in keep),
        provenance=configuration.provenance +
        f"; Gaussian noise sigma={sigma}; {len(configuration.positions)-len(keep)} atoms hidden")


def _centroid(points: Sequence[Vector]) -> Vector:
    return tuple(sum(point[axis] for point in points) / len(points)
                 for axis in range(3))  # type: ignore[return-value]


def _registered_score(
    predicted: AtomicConfiguration,
    target: AtomicConfiguration,
    tolerance: float,
    registration_shift: Optional[Tuple[float, float, float]] = None,
) -> Tuple[float, float, float, float]:
    """Score after evaluator-only optimal translation and one-to-one matching."""
    predicted_center, target_center = (_centroid(predicted.positions),
                                       _centroid(target.positions))
    shift = registration_shift or tuple(
        target_center[axis] - predicted_center[axis] for axis in range(3))
    shifted = [tuple(point[axis] + shift[axis] for axis in range(3))
               for point in predicted.positions]
    cell = tolerance

    def key(point: Vector) -> Tuple[int, int, int]:
        return tuple(int(math.floor(value / cell)) for value in point)  # type: ignore[return-value]

    buckets: Dict[Tuple[int, int, int], list[int]] = {}
    for index, point in enumerate(target.positions):
        buckets.setdefault(key(point), []).append(index)
    available = set(range(len(target.positions)))
    matched = []
    correct_species = 0
    for predicted_index, point in enumerate(shifted):
        base = key(point)
        candidates = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for target_index in buckets.get(
                            (base[0] + dx, base[1] + dy, base[2] + dz), ()):
                        if target_index not in available:
                            continue
                        distance = math.sqrt(sum(
                            (point[axis] - target.positions[target_index][axis]) ** 2
                            for axis in range(3)))
                        if distance <= tolerance:
                            candidates.append((
                                predicted.species[predicted_index] !=
                                target.species[target_index], distance,
                                target_index))
        if not candidates:
            continue
        species_error, distance, target_index = min(candidates)
        available.remove(target_index)
        matched.append(distance)
        correct_species += not species_error
    return (len(matched) / max(1, len(predicted.positions)),
            len(matched) / max(1, len(target.positions)),
            correct_species / max(1, len(matched)),
            math.sqrt(sum(distance * distance for distance in matched) /
                      max(1, len(matched))))


def _score_atlas(atlas: GenericPlanarAtlas, target: AtomicConfiguration,
                 radius: float, ablate_pose: bool = False,
                 registration_shift: Optional[Tuple[float, float, float]] = None
                 ) -> Tuple[float, ...]:
    predicted = grow(atlas, radius,
                     retain_one_pose_per_isometry_class=ablate_pose)
    return _registered_score(predicted, target, tolerance=.16,
                             registration_shift=registration_shift)


def evaluate() -> PlanarRobustnessCase:
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    angles = (0.0, math.pi / 6)
    clean_seed = layered_hexagonal_configuration(
        "hBN-30deg-clean-seed", 18.0, basis, angles,
        global_rotation=True)
    observed = corrupt_seed(clean_seed, sigma=.006,
                            missing_fraction=.035, seed=703)
    atlas = learn_planar_atlas(observed, tolerance=.045)
    target = layered_hexagonal_configuration(
        "hBN-30deg-clean-heldout", 36.0, basis, angles,
        global_rotation=True)
    full_prediction = grow(atlas, 36.0)
    predicted_center, target_center = (_centroid(full_prediction.positions),
                                       _centroid(target.positions))
    registration_shift = tuple(target_center[axis] - predicted_center[axis]
                               for axis in range(3))
    precision, recall, chemistry, rms = _registered_score(
        full_prediction, target, tolerance=.16,
        registration_shift=registration_shift)
    _, ablated_recall, _, _ = _score_atlas(
        atlas, target, 36.0, ablate_pose=True,
        registration_shift=registration_shift)
    return PlanarRobustnessCase(
        "hBN-30deg-noisy-vacancy-seed", len(clean_seed.positions),
        len(observed.positions), len(target.positions), .006,
        1 - len(observed.positions) / len(clean_seed.positions),
        len(atlas.components), tuple(len(component.motif)
                                     for component in atlas.components),
        min(min(component.translation_support)
            for component in atlas.components),
        precision, recall, chemistry, rms, ablated_recall,
        recall - ablated_recall, False, False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
