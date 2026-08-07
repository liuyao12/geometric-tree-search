#!/usr/bin/env python3
"""Recursive, lattice-free cluster and boundary-marking benchmark.

This module is deliberately narrower than a material generator.  Its input is
only a finite colored point set.  Around every point it builds an overlapping
cluster, replaces the children by their learned cluster colors, enlarges the
domain, and repeats.  A marking is the learned discrete section in the annulus
just outside a cluster; it describes which colored clusters can continue it.

The hierarchy is an *implicit* representation.  Expanding it to N explicit
atoms still costs O(N); exponential amplification means that one level-L
macro decision refers to a support whose size grows geometrically with L.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from statistics import median
from typing import DefaultDict, Hashable, Iterable, Sequence, Tuple

Point = Tuple[float, float, float]
Signature = Tuple[object, ...]
Marking = Tuple[Tuple[int, int], ...]


@dataclass(frozen=True)
class RecursiveClusterType:
    level: int
    type_id: int
    signature: Signature
    occurrence_centers: Tuple[int, ...]
    representative_support: Tuple[int, ...]
    learned_marking: Marking
    marking_confidence: float


@dataclass(frozen=True)
class HierarchyLevel:
    level: int
    radius: float
    cluster_types: int
    recurring_types: int
    promoted_types: int
    recurring_centers: int
    recurring_center_fraction: float
    largest_recurring_support: int
    median_recurring_support: float
    learned_marking_types: int
    marking_confidence: float
    recurring_cover_fraction: float
    greedy_macro_decisions: int
    atoms_per_macro_decision: float


@dataclass(frozen=True)
class HierarchyResult:
    system: str
    atoms: int
    chemical_species: int
    nearest_neighbor_scale: float
    levels: Tuple[HierarchyLevel, ...]
    support_amplification: Tuple[float, ...]
    geometric_amplification: bool
    rotation_invariant: bool


@dataclass(frozen=True)
class BenchmarkResult:
    crystal: HierarchyResult
    quasicrystal: HierarchyResult
    amorphous: HierarchyResult


def _distance(left: Sequence[float], right: Sequence[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _distance_table(points: Sequence[Sequence[float]]) -> Tuple[Tuple[float, ...], ...]:
    rows = [[0.0] * len(points) for _ in points]
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            value = _distance(points[left], points[right])
            rows[left][right] = value
            rows[right][left] = value
    return tuple(tuple(row) for row in rows)


def _quantize(value: float, tolerance: float) -> int:
    # The offset avoids platform-level last-bit noise changing bins when a
    # symmetry value lies exactly on a half-bin boundary.
    return int(math.floor(value / tolerance + 0.5001))


def _nearest_neighbor_scale(distances: Sequence[Sequence[float]]) -> float:
    nearest = [min(value for other, value in enumerate(row)
                   if other != center)
               for center, row in enumerate(distances)]
    return median(nearest)


def _stable_species_labels(species: Sequence[Hashable]) -> Tuple[int, ...]:
    keys = sorted({(type(value).__module__, type(value).__qualname__, repr(value))
                   for value in species})
    lookup = {key: index for index, key in enumerate(keys)}
    return tuple(lookup[(type(value).__module__, type(value).__qualname__, repr(value))]
                 for value in species)


def _greedy_union_cover(
    supports: Iterable[Sequence[int]], point_count: int,
) -> Tuple[int, int]:
    remaining = set(range(point_count))
    candidates = [frozenset(support) for support in supports]
    decisions = 0
    while remaining:
        best = max(candidates, key=lambda support: len(support & remaining),
                   default=frozenset())
        gain = len(best & remaining)
        if gain == 0:
            break
        remaining.difference_update(best)
        decisions += 1
    return point_count - len(remaining), decisions


def learn_recursive_hierarchy(
    system: str,
    positions: Sequence[Sequence[float]],
    species: Sequence[Hashable],
    *,
    maximum_levels: int = 4,
    radius_growth: float = 1.85,
    first_radius_scale: float = 1.08,
    marking_width_scale: float = 0.72,
    minimum_occurrences: int = 2,
    minimum_cluster_size: int = 3,
    maximum_promoted_types: int = 4,
    macro_distance_bin_scale: float = 0.08,
    macro_angle_bin: float = 0.05,
    first_descriptor_bin_scale: float = 1e-5,
    first_angle_bin: float = 1e-4,
) -> Tuple[HierarchyResult, Tuple[Tuple[RecursiveClusterType, ...], ...]]:
    """Learn clusters, clusters of clusters, and bounded halo markings.

    No lattice, axes, unit cell, or generator labels are accepted.  Distances
    make the learned colors and markings invariant under rigid motion.  The
    domain grows geometrically, but remains bounded at every level.
    """
    if len(positions) != len(species) or not positions:
        raise ValueError("positions and species must be nonempty and aligned")
    if (maximum_levels < 1 or radius_growth <= 1.0 or
            first_descriptor_bin_scale <= 0.0 or first_angle_bin <= 0.0):
        raise ValueError("invalid hierarchy dimensions")
    points = tuple(tuple(float(value) for value in point) for point in positions)
    distances = _distance_table(points)
    scale = _nearest_neighbor_scale(distances)
    tolerance = max(1e-9, scale * 1e-5)
    labels = _stable_species_labels(species)
    levels = []
    dictionaries = []
    largest_supports = []

    for level in range(1, maximum_levels + 1):
        radius = scale * first_radius_scale * radius_growth ** (level - 1)
        marking_outer = radius + scale * marking_width_scale
        descriptor_bin = (scale * first_descriptor_bin_scale if level == 1
                          else scale * macro_distance_bin_scale)
        angle_bin = first_angle_bin if level == 1 else macro_angle_bin
        grouped: DefaultDict[Signature, list[Tuple[int, Tuple[int, ...], Marking]]] = defaultdict(list)
        for center, row in enumerate(distances):
            support = tuple(index for index, value in enumerate(row)
                            if value <= radius + tolerance)
            # The colored radial section is augmented by a bounded angular
            # fingerprint.  This avoids confusing genuinely different 3-D
            # arrangements that happen to share the same radial shells.
            body = tuple(sorted(
                (labels[index], _quantize(row[index], descriptor_bin))
                for index in support if index != center))
            ranked = sorted((row[index], index) for index in support
                            if index != center)
            nominal = min(12, len(ranked))
            angular_cutoff = (ranked[nominal - 1][0] if nominal else -1.0)
            # Preserve a complete coordination shell; cutting an equal-radius
            # shell by array index would destroy rotation invariance.
            nearest = [item for item in ranked
                       if item[0] <= angular_cutoff + tolerance]
            angular = []
            for left_offset, (left_radius, left) in enumerate(nearest):
                for right_radius, right in nearest[left_offset + 1:]:
                    cosine = ((left_radius * left_radius + right_radius * right_radius
                               - distances[left][right] * distances[left][right]) /
                              (2.0 * left_radius * right_radius))
                    angular.append((min(labels[left], labels[right]),
                                    max(labels[left], labels[right]),
                                    _quantize(cosine, angle_bin)))
            signature: Signature = (labels[center], body, tuple(sorted(angular)))
            marking = tuple(sorted(
                (labels[index], _quantize(row[index] - radius, descriptor_bin))
                for index in range(len(row))
                if radius + tolerance < row[index] <= marking_outer + tolerance))
            grouped[signature].append((center, support, marking))

        ordered = sorted(grouped.items(), key=lambda item: repr(item[0]))
        raw_labels = [0] * len(points)
        models = []
        recurring_supports = []
        marking_weight = 0
        marking_agreement = 0
        recurring_centers = 0
        recurring_type_count = 0
        marking_types = set()
        for type_id, (signature, occurrences) in enumerate(ordered):
            for center, _, _ in occurrences:
                raw_labels[center] = type_id
            markings = Counter(marking for _, _, marking in occurrences)
            learned_marking, agreement = max(
                markings.items(), key=lambda item: (item[1], repr(item[0])))
            count = len(occurrences)
            support_size = len(occurrences[0][1])
            if count >= minimum_occurrences and support_size >= minimum_cluster_size:
                recurring_type_count += 1
                recurring_centers += count
                recurring_supports.extend(support for _, support, _ in occurrences)
                marking_types.add(learned_marking)
                marking_weight += count
                marking_agreement += agreement
            models.append(RecursiveClusterType(
                level=level,
                type_id=type_id,
                signature=signature,
                occurrence_centers=tuple(center for center, _, _ in occurrences),
                representative_support=occurrences[0][1],
                learned_marking=learned_marking,
                marking_confidence=agreement / count,
            ))
        covered, decisions = _greedy_union_cover(recurring_supports, len(points))
        # A finite learned vocabulary is essential: recursively propagating
        # every boundary-specific color causes a combinatorial type explosion.
        # Keep the most evidenced cluster colors and fold the long tail into a
        # single unresolved color for the next level.
        ranked_types = sorted(
            range(len(ordered)),
            key=lambda type_id: (-len(ordered[type_id][1]),
                                 repr(ordered[type_id][0])))
        promoted = [type_id for type_id in ranked_types
                    if (len(ordered[type_id][1]) >= minimum_occurrences and
                        len(ordered[type_id][1][0][1]) >= minimum_cluster_size)][
                        :maximum_promoted_types]
        promoted_lookup = {type_id: rank for rank, type_id in enumerate(promoted)}
        unresolved = len(promoted_lookup)
        new_labels = tuple(promoted_lookup.get(type_id, unresolved)
                           for type_id in raw_labels)
        support_sizes = [len(support) for support in recurring_supports]
        largest = max(support_sizes, default=0)
        largest_supports.append(largest)
        levels.append(HierarchyLevel(
            level=level,
            radius=radius,
            cluster_types=len(ordered),
            recurring_types=recurring_type_count,
            promoted_types=len(promoted),
            recurring_centers=recurring_centers,
            recurring_center_fraction=recurring_centers / len(points),
            largest_recurring_support=largest,
            median_recurring_support=median(support_sizes) if support_sizes else 0.0,
            learned_marking_types=len(marking_types),
            marking_confidence=(marking_agreement / marking_weight
                                if marking_weight else 0.0),
            recurring_cover_fraction=covered / len(points),
            greedy_macro_decisions=decisions,
            atoms_per_macro_decision=(covered / decisions if decisions else 0.0),
        ))
        dictionaries.append(tuple(models))
        labels = new_labels

    amplification = tuple(
        largest_supports[index] / largest_supports[index - 1]
        if largest_supports[index - 1] else 0.0
        for index in range(1, len(largest_supports)))
    positive = [value for value in amplification if value > 0.0]
    geometric = (len(positive) >= 2 and median(positive) >= 2.0 and
                 largest_supports[-1] >= 32)
    result = HierarchyResult(
        system=system,
        atoms=len(points),
        chemical_species=len(set(species)),
        nearest_neighbor_scale=scale,
        levels=tuple(levels),
        support_amplification=amplification,
        geometric_amplification=geometric,
        rotation_invariant=True,
    )
    return result, tuple(dictionaries)


def _rotate(points: Sequence[Sequence[float]]) -> Tuple[Point, ...]:
    # Fixed proper rotation followed by translation.
    return tuple((-point[1] + 3.25, point[0] - 1.5, point[2] + 0.75)
                 for point in points)


def _with_rotation_check(
    name: str, positions: Sequence[Sequence[float]], species: Sequence[Hashable],
) -> HierarchyResult:
    result, _ = learn_recursive_hierarchy(name, positions, species)
    moved, _ = learn_recursive_hierarchy(name, _rotate(positions), species)
    invariant = tuple(
        (level.cluster_types, level.recurring_types,
         level.largest_recurring_support, level.learned_marking_types)
        for level in result.levels
    ) == tuple(
        (level.cluster_types, level.recurring_types,
         level.largest_recurring_support, level.learned_marking_types)
        for level in moved.levels)
    return HierarchyResult(**{**asdict(result), "levels": result.levels,
                              "support_amplification": result.support_amplification,
                              "rotation_invariant": invariant})


def evaluate() -> BenchmarkResult:
    from materials_gcts_icosahedral_modelset import oracle_patch
    from materials_pointset_benchmarks import (
        amorphous_hard_core_point_set, crystalline_control)

    crystal = crystalline_control(shell_radius=5)
    iqc, _ = oracle_patch(3, 9.0)
    amorphous = amorphous_hard_core_point_set(atom_count=507)
    return BenchmarkResult(
        crystal=_with_rotation_check(
            crystal.name, crystal.positions, crystal.species),
        quasicrystal=_with_rotation_check(
            iqc.name, iqc.positions, iqc.species),
        amorphous=_with_rotation_check(
            amorphous.name, amorphous.positions, amorphous.species),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if arguments.json else result)


if __name__ == "__main__":
    main()
