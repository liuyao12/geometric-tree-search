#!/usr/bin/env python3
"""Train-only frozen recursive color encoder for large atomic point clouds."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from statistics import median
from typing import DefaultDict, Hashable, Sequence, Tuple

from materials_gcts_guarded_spatial_split import guarded_center_indices


Signature = Tuple[object, ...]


@dataclass
class FrozenLevelEncoder:
    level: int
    radius: float
    marking_outer: float
    known_signatures: int
    promoted_types: int
    unknown_label: int
    training_centers: int
    _signature_to_label: dict[Signature, int] = field(repr=False)
    _known_signatures: frozenset[Signature] = field(repr=False)


@dataclass
class FrozenHierarchyEncoder:
    nearest_neighbor_scale: float
    species_labels: dict[str, int]
    levels: Tuple[FrozenLevelEncoder, ...]
    maximum_promoted_types: int
    promotion_coverage_target: float


@dataclass(frozen=True)
class FrozenTransferLevel:
    level: int
    training_centers: int
    heldout_centers: int
    known_training_fraction: float
    known_heldout_fraction: float
    heldout_promoted_fraction: float
    frozen_types: int
    promoted_types: int
    heldout_refit_used: bool


@dataclass(frozen=True)
class FrozenTransferCase:
    system: str
    atoms: int
    levels: Tuple[FrozenTransferLevel, ...]
    minimum_heldout_known_fraction: float
    minimum_heldout_centers: int
    frozen_encoder_reused: bool
    benchmark_passed: bool


@dataclass(frozen=True)
class FrozenHierarchyBenchmark:
    crystal: FrozenTransferCase
    quasicrystal: FrozenTransferCase
    both_transfer_without_refit: bool
    benchmark_passed: bool


def _species_key(value: Hashable) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _quantize(value: float, width: float) -> int:
    return int(math.floor(value / width + .5001))


class _SpatialIndex:
    def __init__(self, points, cell):
        self.points = points
        self.cell = cell
        self.grid: DefaultDict[tuple[int, int, int], list[int]] = defaultdict(list)
        for index, point in enumerate(points):
            self.grid[self.key(point)].append(index)

    def key(self, point):
        return tuple(math.floor(value / self.cell) for value in point)

    def within(self, center: int, radius: float):
        point = self.points[center]
        key = self.key(point)
        reach = math.ceil(radius / self.cell)
        result = []
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                for dz in range(-reach, reach + 1):
                    for index in self.grid.get(
                            (key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        distance = math.dist(point, self.points[index])
                        if distance <= radius + 1e-9:
                            result.append((distance, index))
        return tuple(sorted(result))


def _training_scale(points, centers) -> float:
    sample = centers[::max(1, len(centers) // 96)][:96]
    nearest = []
    for center in sample:
        nearest.append(min(math.dist(points[center], point)
                           for index, point in enumerate(points)
                           if index != center))
    return median(nearest)


def _signature(index, support, labels, points, descriptor_bin, angle_bin):
    center_label = labels[index]
    body = tuple(sorted((labels[other], _quantize(distance, descriptor_bin))
                        for distance, other in support if other != index))
    ranked = [(distance, other) for distance, other in support
              if other != index]
    nominal = min(12, len(ranked))
    cutoff = ranked[nominal - 1][0] if nominal else -1.0
    nearest = [item for item in ranked if item[0] <= cutoff + 1e-9]
    angular = []
    for offset, (left_radius, left) in enumerate(nearest):
        for right_radius, right in nearest[offset + 1:]:
            cosine = ((left_radius ** 2 + right_radius ** 2 -
                       math.dist(points[left], points[right]) ** 2) /
                      (2 * left_radius * right_radius))
            angular.append((min(labels[left], labels[right]),
                            max(labels[left], labels[right]),
                            _quantize(cosine, angle_bin)))
    return center_label, body, tuple(sorted(angular))


def _all_signatures(points, labels, index, radius, descriptor_bin, angle_bin):
    return tuple(_signature(center, index.within(center, radius), labels,
                            points, descriptor_bin, angle_bin)
                 for center in range(len(points)))


def fit_frozen_hierarchy(configuration, maximum_levels=3,
                         maximum_promoted_types=64,
                         promotion_coverage_target=.95):
    points = configuration.positions
    train_by_level = tuple(guarded_center_indices(configuration, level, "train")
                           for level in range(1, maximum_levels + 1))
    scale = _training_scale(points, train_by_level[0])
    species_keys = tuple(_species_key(value) for value in configuration.species)
    ordered_species = sorted({species_keys[index]
                              for index in train_by_level[0]})
    species_map = {chemical: index for index, chemical in enumerate(ordered_species)}
    unknown_species = len(species_map)
    labels = tuple(species_map.get(chemical, unknown_species)
                   for chemical in species_keys)
    spatial = _SpatialIndex(points, scale)
    levels = []
    known_masks = []
    for offset in range(maximum_levels):
        radius = scale * 1.08 * 1.85 ** offset
        descriptor = scale * (.02 if offset == 0 else .20)
        angle = .03 if offset == 0 else .08
        signatures = _all_signatures(
            points, labels, spatial, radius, descriptor, angle)
        counts = Counter(signatures[index] for index in train_by_level[offset])
        ranked = sorted(counts, key=lambda signature: (-counts[signature],
                                                       repr(signature)))
        recurring = [signature for signature in ranked
                     if counts[signature] >= 2]
        promoted = []
        covered = 0
        target = promotion_coverage_target * len(train_by_level[offset])
        for signature in recurring:
            if len(promoted) >= maximum_promoted_types:
                break
            promoted.append(signature)
            covered += counts[signature]
            if covered >= target:
                break
        lookup = {signature: label for label, signature in enumerate(promoted)}
        unknown = len(lookup)
        known = frozenset(counts)
        levels.append(FrozenLevelEncoder(
            offset + 1, radius, radius + scale * .72, len(known),
            len(promoted), unknown, len(train_by_level[offset]), lookup,
            known))
        known_masks.append(tuple(signature in known for signature in signatures))
        labels = tuple(lookup.get(signature, unknown) for signature in signatures)
    return FrozenHierarchyEncoder(
        scale, species_map, tuple(levels), maximum_promoted_types,
        promotion_coverage_target), known_masks


def encode_frozen_hierarchy(configuration, encoder):
    points = configuration.positions
    species_keys = tuple(_species_key(value) for value in configuration.species)
    unknown_species = len(encoder.species_labels)
    labels = tuple(encoder.species_labels.get(value, unknown_species)
                   for value in species_keys)
    spatial = _SpatialIndex(points, encoder.nearest_neighbor_scale)
    results = []
    level_labels = []
    for offset, level in enumerate(encoder.levels):
        descriptor = encoder.nearest_neighbor_scale * (.02 if offset == 0 else .20)
        angle = .03 if offset == 0 else .08
        signatures = _all_signatures(
            points, labels, spatial, level.radius, descriptor, angle)
        known = tuple(signature in level._known_signatures
                      for signature in signatures)
        promoted = tuple(signature in level._signature_to_label
                         for signature in signatures)
        labels = tuple(level._signature_to_label.get(signature,
                                                     level.unknown_label)
                       for signature in signatures)
        results.append((known, promoted))
        level_labels.append(labels)
    return tuple(results), tuple(level_labels)


def transform_frozen_hierarchy(configuration, encoder):
    return encode_frozen_hierarchy(configuration, encoder)[0]


def _case(configuration, maximum_levels=3):
    encoder, training_known = fit_frozen_hierarchy(
        configuration, maximum_levels=maximum_levels)
    heldout_promoted = transform_frozen_hierarchy(configuration, encoder)
    rows = []
    for offset, level in enumerate(encoder.levels):
        train = guarded_center_indices(configuration, offset + 1, "train")
        heldout = guarded_center_indices(configuration, offset + 1, "heldout")
        train_fraction = sum(training_known[offset][index]
                             for index in train) / len(train)
        heldout_fraction = sum(heldout_promoted[offset][0][index]
                               for index in heldout) / len(heldout)
        promoted_fraction = sum(heldout_promoted[offset][1][index]
                                for index in heldout) / len(heldout)
        rows.append(FrozenTransferLevel(
            offset + 1, len(train), len(heldout), train_fraction,
            heldout_fraction, promoted_fraction, level.known_signatures,
            level.promoted_types, False))
    minimum = min(row.known_heldout_fraction for row in rows)
    passed = (minimum >= .99 and
              min(row.heldout_promoted_fraction for row in rows) >= .90 and
              all(not row.heldout_refit_used for row in rows))
    return FrozenTransferCase(
        configuration.name, len(configuration.positions), tuple(rows), minimum,
        min(row.heldout_centers for row in rows), True, passed)


def evaluate():
    from materials_gcts_generic import benchmark_systems
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_gcts_periodic_growth import replicate

    crystal = next(item for item in benchmark_systems()
                   if item.name == "NaCl-rocksalt")
    crystal = replicate(replicate(crystal))
    unit = (1 + math.sqrt(5)) / 2
    quasicrystal, _ = oracle_patch(6, 9 * unit ** 2)
    cases = _case(crystal, 3), _case(quasicrystal, 2)
    transfer = all(case.frozen_encoder_reused for case in cases)
    return FrozenHierarchyBenchmark(
        *cases, transfer,
        transfer and all(case.benchmark_passed for case in cases))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
