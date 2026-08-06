#!/usr/bin/env python3
"""Lattice-agnostic local-cluster discovery for colored 3D point sets.

The learner deliberately accepts no unit cell, fractional coordinates, lattice
indices, or preferred frame.  It builds a bounded environment around every
point and groups environments by a species-labelled, rotation-invariant
distance descriptor.  Occurrences are independent supports and may overlap;
selecting a globally consistent cover is left to the downstream GCTS layer.

This is a candidate learner rather than a claim of complete graph canonization:
the descriptor is a deterministic Weisfeiler--Lehman-like fingerprint of the
complete local distance graph.  It includes central distances and all
neighbor--neighbor distances, and therefore also contains the local angular
information through the law of cosines.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Hashable, Optional, Sequence, Tuple

Point = Tuple[float, float, float]
SpeciesKey = Tuple[str, str]
EdgeFingerprint = Tuple[SpeciesKey, int]
NeighborFingerprint = Tuple[SpeciesKey, int, Tuple[EdgeFingerprint, ...]]
LocalSignature = Tuple[SpeciesKey, Tuple[NeighborFingerprint, ...]]
DistanceMatrix = Tuple[Tuple[float, ...], ...]


@dataclass(frozen=True)
class ClusterOccurrence:
    """One candidate cluster, anchored at ``center_index``.

    ``member_indices`` starts with the center.  Different occurrences are
    intentionally allowed to share members.
    """

    center_index: int
    member_indices: Tuple[int, ...]
    signature: LocalSignature


@dataclass(frozen=True)
class ClusterType:
    """A recurring rotation/translation-invariant local environment type."""

    type_id: int
    center_species: Hashable
    signature: LocalSignature
    representative_center: int
    representative_members: Tuple[int, ...]
    representative_species: Tuple[Hashable, ...]
    representative_distances: DistanceMatrix
    occurrences: Tuple[ClusterOccurrence, ...]


@dataclass(frozen=True)
class ClusterLearningResult:
    """Candidate dictionary and its (possibly overlapping) occurrences."""

    point_count: int
    minimum_distance: float
    cluster_types: Tuple[ClusterType, ...]
    occurrences: Tuple[ClusterOccurrence, ...]


def _point(value: Sequence[float]) -> Point:
    if len(value) != 3:
        raise ValueError("every point must have exactly three coordinates")
    point = tuple(float(coordinate) for coordinate in value)
    if not all(math.isfinite(coordinate) for coordinate in point):
        raise ValueError("point coordinates must be finite")
    return point  # type: ignore[return-value]


def _species_key(value: Hashable) -> SpeciesKey:
    """Provide a total, deterministic ordering for common species labels."""
    try:
        hash(value)
    except TypeError as error:
        raise ValueError("species labels must be hashable") from error
    return (f"{type(value).__module__}.{type(value).__qualname__}", repr(value))


def _distance(left: Point, right: Point) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _quantize(value: float, tolerance: float) -> int:
    return int(round(value / tolerance))


def _distance_table(points: Sequence[Point]) -> Tuple[Tuple[float, ...], ...]:
    rows = [[0.0] * len(points) for _ in points]
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            value = _distance(points[left], points[right])
            rows[left][right] = value
            rows[right][left] = value
    return tuple(tuple(row) for row in rows)


def _members_for_center(
    center: int,
    distances: Sequence[Sequence[float]],
    *,
    neighbor_count: Optional[int],
    radius: Optional[float],
    distance_tolerance: float,
) -> Tuple[int, ...]:
    ranked = sorted(
        ((distances[center][other], other)
         for other in range(len(distances)) if other != center),
        key=lambda item: (item[0], item[1]),
    )
    if radius is not None:
        neighbors = [other for distance, other in ranked
                     if distance <= radius + distance_tolerance]
    else:
        assert neighbor_count is not None
        requested = min(neighbor_count, len(ranked))
        if requested == 0:
            neighbors = []
        else:
            cutoff = ranked[requested - 1][0]
            # Including exact/tolerance ties avoids arbitrary orientation-neutral
            # shells being split by input index.
            neighbors = [other for distance, other in ranked
                         if distance <= cutoff + distance_tolerance]
    return (center,) + tuple(neighbors)


def _signature(
    center: int,
    members: Sequence[int],
    species_keys: Sequence[SpeciesKey],
    distances: Sequence[Sequence[float]],
    descriptor_tolerance: float,
) -> LocalSignature:
    neighbors = members[1:]
    fingerprints = []
    for neighbor in neighbors:
        edges = tuple(sorted(
            (species_keys[other],
             _quantize(distances[neighbor][other], descriptor_tolerance))
            for other in neighbors if other != neighbor
        ))
        fingerprints.append((
            species_keys[neighbor],
            _quantize(distances[center][neighbor], descriptor_tolerance),
            edges,
        ))
    return species_keys[center], tuple(sorted(fingerprints))


def _induced_distances(
    members: Sequence[int],
    distances: Sequence[Sequence[float]],
) -> DistanceMatrix:
    return tuple(tuple(distances[left][right] for right in members)
                 for left in members)


def learn_cluster_candidates(
    species: Sequence[Hashable],
    points: Sequence[Sequence[float]],
    *,
    neighbor_count: Optional[int] = 6,
    radius: Optional[float] = None,
    descriptor_tolerance: float = 1e-6,
    minimum_occurrences: int = 1,
) -> ClusterLearningResult:
    """Discover bounded local cluster types in a finite colored point set.

    Exactly one neighborhood policy is active.  By default, every support
    contains the center and at least its six nearest neighbors.  Neighbors tied
    at the cutoff (within ``descriptor_tolerance``) are included together.
    Passing ``radius`` instead selects every neighbor inside that Euclidean
    radius and requires ``neighbor_count=None``.

    No partition is constructed: every qualifying center produces an
    occurrence, and those occurrence supports may overlap arbitrarily.
    ``minimum_occurrences`` filters the returned candidate dictionary without
    changing how environments are fingerprinted.
    """
    if len(species) != len(points):
        raise ValueError("species and points must have equal length")
    if not points:
        raise ValueError("at least one point is required")
    if descriptor_tolerance <= 0 or not math.isfinite(descriptor_tolerance):
        raise ValueError("descriptor_tolerance must be finite and positive")
    if minimum_occurrences < 1:
        raise ValueError("minimum_occurrences must be positive")
    if radius is None:
        if neighbor_count is None or neighbor_count < 0:
            raise ValueError("neighbor_count must be nonnegative")
    elif neighbor_count is not None:
        raise ValueError("pass either neighbor_count or radius, not both")
    elif radius <= 0 or not math.isfinite(radius):
        raise ValueError("radius must be finite and positive")

    normalized_points = tuple(_point(point) for point in points)
    species_keys = tuple(_species_key(value) for value in species)
    distances = _distance_table(normalized_points)
    pair_distances = [distances[left][right]
                      for left in range(len(points))
                      for right in range(left + 1, len(points))]
    minimum_distance = min(pair_distances, default=math.inf)
    if minimum_distance <= 0.0:
        raise ValueError("points must be distinct with positive separation")

    grouped: DefaultDict[LocalSignature, list[ClusterOccurrence]] = defaultdict(list)
    for center in range(len(points)):
        members = _members_for_center(
            center, distances, neighbor_count=neighbor_count, radius=radius,
            distance_tolerance=descriptor_tolerance)
        signature = _signature(
            center, members, species_keys, distances, descriptor_tolerance)
        grouped[signature].append(ClusterOccurrence(center, members, signature))

    retained = [(signature, tuple(occurrences))
                for signature, occurrences in grouped.items()
                if len(occurrences) >= minimum_occurrences]
    retained.sort(key=lambda item: item[0])
    cluster_types = tuple(
        ClusterType(
            type_id=type_id,
            center_species=species[occurrences[0].center_index],
            signature=signature,
            representative_center=occurrences[0].center_index,
            representative_members=occurrences[0].member_indices,
            representative_species=tuple(
                species[index] for index in occurrences[0].member_indices),
            representative_distances=_induced_distances(
                occurrences[0].member_indices, distances),
            occurrences=occurrences,
        )
        for type_id, (signature, occurrences) in enumerate(retained)
    )
    all_occurrences = tuple(
        occurrence for cluster_type in cluster_types
        for occurrence in cluster_type.occurrences)
    return ClusterLearningResult(
        point_count=len(points),
        minimum_distance=minimum_distance,
        cluster_types=cluster_types,
        occurrences=all_occurrences,
    )


def enumerate_type_occurrences(
    cluster_type: ClusterType,
    species: Sequence[Hashable],
    points: Sequence[Sequence[float]],
    *,
    distance_tolerance: float = 1e-6,
    maximum_occurrences: Optional[int] = None,
) -> Tuple[ClusterOccurrence, ...]:
    """Enumerate colored distance-graph embeddings of ``cluster_type``.

    The representative center (member zero) is anchored at each target point
    of the same species.  Remaining members are assigned by a finite
    backtracking search with species, center-distance, and all already assigned
    pair-distance constraints.  Other target points, including points closer
    to the center than a representative member, impose no constraint: this is
    subgraph matching for covering candidates, not nearest-neighbor matching.

    Symmetries among repeated-species members can produce multiple vertex
    mappings of one geometric occurrence.  Results are therefore deduplicated
    by their unordered target support.
    """
    if len(species) != len(points):
        raise ValueError("species and points must have equal length")
    if distance_tolerance <= 0 or not math.isfinite(distance_tolerance):
        raise ValueError("distance_tolerance must be finite and positive")
    if maximum_occurrences is not None and maximum_occurrences < 1:
        raise ValueError("maximum_occurrences must be positive when supplied")

    target_points = tuple(_point(point) for point in points)
    target_species = tuple(_species_key(value) for value in species)
    reference_species = tuple(
        _species_key(value) for value in cluster_type.representative_species)
    reference_distances = cluster_type.representative_distances
    size = len(reference_species)
    if size == 0 or len(reference_distances) != size or any(
            len(row) != size for row in reference_distances):
        raise ValueError("cluster type has an invalid representative graph")
    target_distances = _distance_table(target_points)

    results = []
    seen_supports = set()
    stop = False
    for center in range(len(points)):
        if target_species[center] != reference_species[0]:
            continue
        mapping = [-1] * size
        mapping[0] = center
        used = {center}
        candidates = {reference: tuple(
            target for target in range(len(points))
            if target != center
            and target_species[target] == reference_species[reference]
            and abs(target_distances[center][target] -
                    reference_distances[0][reference]) <= distance_tolerance
        ) for reference in range(1, size)}
        if any(not values for values in candidates.values()):
            continue

        def compatible(reference: int, target: int) -> bool:
            return target not in used and all(
                assigned_target < 0 or
                abs(target_distances[target][assigned_target] -
                    reference_distances[reference][assigned_reference])
                <= distance_tolerance
                for assigned_reference, assigned_target in enumerate(mapping))

        def search() -> None:
            nonlocal stop
            if stop:
                return
            unresolved = [reference for reference in range(1, size)
                          if mapping[reference] < 0]
            if not unresolved:
                support = tuple(sorted(mapping))
                if support not in seen_supports:
                    seen_supports.add(support)
                    results.append(ClusterOccurrence(
                        center_index=mapping[0],
                        member_indices=tuple(mapping),
                        signature=cluster_type.signature,
                    ))
                    if (maximum_occurrences is not None and
                            len(results) >= maximum_occurrences):
                        stop = True
                return
            reference = min(
                unresolved,
                key=lambda item: (
                    sum(compatible(item, target)
                        for target in candidates[item]), item),
            )
            for target in candidates[reference]:
                if not compatible(reference, target):
                    continue
                mapping[reference] = target
                used.add(target)
                search()
                used.remove(target)
                mapping[reference] = -1
                if stop:
                    return

        search()
        if stop:
            break
    return tuple(results)


def occurrence_type_labels(result: ClusterLearningResult) -> Tuple[int, ...]:
    """Return the learned type at each center, using ``-1`` if filtered out."""
    labels = [-1] * result.point_count
    for cluster_type in result.cluster_types:
        for occurrence in cluster_type.occurrences:
            labels[occurrence.center_index] = cluster_type.type_id
    return tuple(labels)
