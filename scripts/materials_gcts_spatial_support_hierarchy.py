#!/usr/bin/env python3
"""Generic recursive hierarchy from disjoint colored spatial point domains.

The learner accepts only positions, species, domain labels, and bounded radii.
It builds connected covers at the first radius, then connects those clusters at
successively larger radii.  Thus every level is literally a cover by clusters
of the preceding level.  Rigid type identity uses colored pair distances and
does not depend on a lattice, axes, atom indices, or construction order.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Hashable, Mapping, Optional, Sequence, Tuple


Point = Tuple[float, float, float]
Signature = Tuple[object, ...]


@dataclass(frozen=True)
class SpatialClusterOccurrence:
    domain: Hashable
    support: Tuple[int, ...]
    geometry_type: Signature
    child_types: Tuple[Signature, ...]


@dataclass(frozen=True)
class SpatialSupportLevel:
    level: int
    radius: float
    occurrences: Tuple[SpatialClusterOccurrence, ...]
    geometry_types: int
    recurrent_types: int
    recurrent_occurrences: int
    largest_recurrent_support: int
    recurrent_atom_coverage: float
    exact_child_cover: bool


@dataclass(frozen=True)
class SpatialSupportHierarchy:
    atoms: int
    assigned_atoms: int
    domains: int
    nearest_neighbor_scale: float
    radii: Tuple[float, ...]
    levels: Tuple[SpatialSupportLevel, ...]
    hierarchy_depth: int
    support_amplification: Tuple[float, ...]
    complete_cover_each_level: bool
    rigid_motion_invariant: bool
    construction_order_used: bool


def _distance_squared(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right))


def nearest_neighbor_scale(positions: Sequence[Sequence[float]]) -> float:
    nearest = []
    for index, point in enumerate(positions):
        nearest.append(min(
            math.sqrt(_distance_squared(point, other))
            for other_index, other in enumerate(positions)
            if other_index != index))
    return median(nearest)


def colored_isometry_signature(
    positions: Sequence[Sequence[float]],
    species: Sequence[Hashable],
    support: Sequence[int],
    length_unit: float,
    tolerance_scale: float = 1e-5,
) -> Signature:
    """Quantized invariant fingerprint for a finite colored point set.

    The colored distance multiset is permutation and rigid-motion invariant.
    It is used as a fast type key here; a production learner must still resolve
    rare homometric collisions with an explicit congruence check. Chirality is
    intentionally not distinguished at this stage; a later proper-frame port
    rule may split enantiomorphic attachments.
    """
    quantization = max(1e-10, length_unit * tolerance_scale)
    colors = tuple(sorted(repr(species[index]) for index in support))
    pairs = []
    for offset, left in enumerate(support):
        for right in support[offset + 1:]:
            color_pair = tuple(sorted(
                (repr(species[left]), repr(species[right]))))
            distance = math.sqrt(_distance_squared(
                positions[left], positions[right]))
            pairs.append((color_pair, round(distance / quantization)))
    return len(support), colors, tuple(sorted(pairs))


def _connected_components(nodes, positions, radius):
    radius_squared = radius * radius + 1e-10
    adjacency = [[] for _ in nodes]
    for left_index, left in enumerate(nodes):
        for right_index in range(left_index + 1, len(nodes)):
            right = nodes[right_index]
            if min(_distance_squared(positions[a], positions[b])
                   for a in left.support for b in right.support) <= radius_squared:
                adjacency[left_index].append(right_index)
                adjacency[right_index].append(left_index)
    unseen = set(range(len(nodes)))
    components = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        stack = [seed]
        component = []
        while stack:
            index = stack.pop()
            component.append(index)
            for neighbor in adjacency[index]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(components)


def learn_spatial_support_hierarchy(
    positions: Sequence[Sequence[float]],
    species: Sequence[Hashable],
    domains: Mapping[Hashable, Sequence[int]],
    *,
    radius_scales: Sequence[float] = (1.08, 2.0, 3.7),
    minimum_domains: int = 2,
    minimum_occurrences: int = 2,
    frozen_length_unit: Optional[float] = None,
) -> SpatialSupportHierarchy:
    if not positions or len(positions) != len(species):
        raise ValueError("positions and species must be nonempty and aligned")
    if not domains or any(scale <= 0 for scale in radius_scales):
        raise ValueError("domains and positive radius scales are required")
    normalized = tuple(tuple(float(value) for value in point)
                       for point in positions)
    assigned = set(index for indices in domains.values()
                   for index in set(indices))
    if any(index < 0 or index >= len(normalized) for index in assigned):
        raise ValueError("domain index out of range")
    if sum(len(set(indices)) for indices in domains.values()) != len(assigned):
        raise ValueError("spatial hierarchy domains must be disjoint")
    if len(assigned) < 2:
        raise ValueError("at least two assigned atoms are required")
    unit = (frozen_length_unit if frozen_length_unit is not None else
            nearest_neighbor_scale(tuple(normalized[index]
                                         for index in sorted(assigned))))
    if unit <= 0:
        raise ValueError("length unit must be positive")
    radii = tuple(unit * scale for scale in radius_scales)
    domain_nodes = {
        label: tuple(SpatialClusterOccurrence(
            label, (index,),
            colored_isometry_signature(normalized, species, (index,), unit),
            ()) for index in sorted(set(indices)))
        for label, indices in domains.items()
    }

    levels = []
    largest = []
    complete = True
    for level, radius in enumerate(radii, 1):
        occurrences = []
        next_nodes = {}
        level_complete = True
        for domain, nodes in domain_nodes.items():
            produced = []
            for component in _connected_components(nodes, normalized, radius):
                children = tuple(nodes[index] for index in component)
                support = tuple(sorted({atom for child in children
                                        for atom in child.support}))
                geometry = colored_isometry_signature(
                    normalized, species, support, unit)
                occurrence = SpatialClusterOccurrence(
                    domain, support, geometry,
                    tuple(sorted((child.geometry_type for child in children),
                                 key=repr)))
                produced.append(occurrence)
                occurrences.append(occurrence)
            next_nodes[domain] = tuple(produced)
            covered = {atom for occurrence in produced
                       for atom in occurrence.support}
            expected = {atom for node in nodes for atom in node.support}
            level_complete &= covered == expected and sum(
                len(occurrence.support) for occurrence in produced) == len(expected)
        complete &= level_complete

        counts = Counter(item.geometry_type for item in occurrences)
        type_domains = defaultdict(set)
        for occurrence in occurrences:
            type_domains[occurrence.geometry_type].add(occurrence.domain)
        recurrent = {signature for signature, count in counts.items()
                     if count >= minimum_occurrences and
                     len(type_domains[signature]) >= minimum_domains}
        recurrent_occurrences = [item for item in occurrences
                                 if item.geometry_type in recurrent]
        recurrent_atoms = {atom for item in recurrent_occurrences
                           for atom in item.support}
        maximum = max((len(item.support) for item in recurrent_occurrences),
                      default=0)
        largest.append(maximum)
        levels.append(SpatialSupportLevel(
            level, radius, tuple(occurrences), len(counts), len(recurrent),
            len(recurrent_occurrences), maximum,
            len(recurrent_atoms) / max(1, len(assigned)), level_complete))
        domain_nodes = next_nodes

    depth = 0
    prior = 1
    for item in levels:
        if item.recurrent_types and item.largest_recurrent_support > prior:
            depth += 1
            prior = item.largest_recurrent_support
        else:
            break
    amplification = tuple(
        largest[index] / largest[index - 1]
        for index in range(1, len(largest))
        if largest[index - 1] > 0)
    return SpatialSupportHierarchy(
        len(normalized), len(assigned), len(domains), unit, radii,
        tuple(levels), depth, amplification, complete, True, False)


def guarded_octants(
    positions: Sequence[Sequence[float]], margin: float,
    center: Optional[Sequence[float]] = None,
) -> Mapping[Tuple[bool, bool, bool], Tuple[int, ...]]:
    """Create eight disjoint spatial evaluation domains, excluding planes."""
    center = (tuple(float(value) for value in center) if center is not None else
              tuple(median(point[axis] for point in positions)
                    for axis in range(3)))
    grouped = defaultdict(list)
    for index, point in enumerate(positions):
        delta = tuple(point[axis] - center[axis] for axis in range(3))
        if any(abs(value) <= margin for value in delta):
            continue
        grouped[tuple(value > 0 for value in delta)].append(index)
    return {key: tuple(values) for key, values in grouped.items()}
