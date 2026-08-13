#!/usr/bin/env python3
"""Leakage-resistant spatial domains for frozen GCTS evaluation."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from statistics import median
from typing import Sequence, Tuple

from materials_gcts_generic import AtomicConfiguration, benchmark_systems
from materials_gcts_icosahedral_modelset import oracle_patch
from materials_gcts_periodic_growth import replicate


Point = Tuple[float, float, float]
NORMAL = tuple(value / math.sqrt(14.0) for value in (1.0, 2.0, 3.0))


@dataclass(frozen=True)
class GuardedLevel:
    level: int
    body_radius: float
    halo_width: float
    guarded_radius: float
    training_centers: int
    heldout_centers: int
    buffer_centers: int
    train_test_center_separation: float
    domains_provably_disjoint: bool


@dataclass(frozen=True)
class GuardedCase:
    system: str
    atoms: int
    nearest_neighbor_scale: float
    levels: Tuple[GuardedLevel, ...]
    minimum_training_centers: int
    minimum_heldout_centers: int
    all_domains_disjoint: bool


@dataclass(frozen=True)
class GuardedSpatialBenchmark:
    crystal: GuardedCase
    quasicrystal: GuardedCase
    fixed_plane_normal: Point
    three_level_split_feasible: bool
    crystal_certified_levels: int
    quasicrystal_certified_levels: int
    benchmark_passed: bool


def _centroid(points: Sequence[Point]) -> Point:
    return tuple(sum(point[axis] for point in points) / len(points)
                 for axis in range(3))  # type: ignore[return-value]


def _projection(point: Point, center: Point) -> float:
    return sum((point[axis] - center[axis]) * NORMAL[axis]
               for axis in range(3))


def _sampled_nearest_scale(points: Sequence[Point], samples: int = 96) -> float:
    offsets = tuple(sorted({round(index * (len(points) - 1) /
                                  max(1, samples - 1))
                            for index in range(min(samples, len(points)))}))
    nearest = []
    for offset in offsets:
        nearest.append(min(math.dist(points[offset], point)
                           for index, point in enumerate(points)
                           if index != offset))
    return median(nearest)


def _case(configuration: AtomicConfiguration) -> GuardedCase:
    points = configuration.positions
    center = _centroid(points)
    scale = _sampled_nearest_scale(points)
    outer_radius = max(math.dist(point, center) for point in points)
    levels = []
    cumulative_body = 0.0
    for level in range(1, 4):
        body = scale * 1.08 * 1.85 ** (level - 1)
        halo = scale * .72
        cumulative_body += body
        guarded = cumulative_body + halo
        eligible_radius = outer_radius - guarded
        projections = tuple(_projection(point, center) for point in points)
        train = tuple(index for index, point in enumerate(points)
                      if projections[index] <= -guarded and
                      math.dist(point, center) <= eligible_radius)
        heldout = tuple(index for index, point in enumerate(points)
                        if projections[index] >= guarded and
                        math.dist(point, center) <= eligible_radius)
        buffer = len(points) - len(train) - len(heldout)
        separation = (min((projections[index] for index in heldout),
                          default=math.inf) -
                      max((projections[index] for index in train),
                          default=-math.inf))
        # A recursive level-L signature depends on raw atoms through all lower
        # body radii, hence the cumulative guard rather than only r_L + halo.
        # Every atom in a radius-guarded training domain has projection <= 0;
        # every atom in a held-out domain has projection >= 0. Strict center
        # separation makes the two closed domains disjoint away from the plane.
        disjoint = bool(train and heldout and separation >= 2 * guarded - 1e-9)
        levels.append(GuardedLevel(
            level, body, halo, guarded, len(train), len(heldout), buffer,
            separation, disjoint))
    return GuardedCase(
        configuration.name, len(points), scale, tuple(levels),
        min(item.training_centers for item in levels),
        min(item.heldout_centers for item in levels),
        all(item.domains_provably_disjoint for item in levels))


def guarded_center_indices(configuration: AtomicConfiguration, level: int,
                           side: str) -> Tuple[int, ...]:
    """Return the predeclared train/held-out centers for one hierarchy level."""
    if level not in (1, 2, 3) or side not in ("train", "heldout"):
        raise ValueError("level must be 1..3 and side train or heldout")
    points = configuration.positions
    center = _centroid(points)
    scale = _sampled_nearest_scale(points)
    cumulative_body = sum(scale * 1.08 * 1.85 ** offset
                          for offset in range(level))
    guarded = cumulative_body + scale * .72
    outer_radius = max(math.dist(point, center) for point in points)
    sign = -1.0 if side == "train" else 1.0
    return tuple(index for index, point in enumerate(points)
                 if sign * _projection(point, center) >= guarded and
                 math.dist(point, center) <= outer_radius - guarded)


def evaluate() -> GuardedSpatialBenchmark:
    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    crystal = replicate(replicate(crystal))
    unit = (1.0 + math.sqrt(5.0)) / 2.0
    quasicrystal, _ = oracle_patch(6, 9.0 * unit ** 2)
    cases = _case(crystal), _case(quasicrystal)
    certified = tuple(sum(item.training_centers >= 100 and
                          item.heldout_centers >= 100 and
                          item.domains_provably_disjoint for item in case.levels)
                      for case in cases)
    feasible = min(certified) >= 3
    passed = certified[0] >= 3 and certified[1] >= 2
    return GuardedSpatialBenchmark(
        *cases, NORMAL, feasible, *certified, passed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
