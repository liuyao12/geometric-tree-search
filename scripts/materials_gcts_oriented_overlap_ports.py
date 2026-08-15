#!/usr/bin/env python3
"""Finite proper-SE(3) overlap ports for colored point-set clusters.

The module deliberately has no material vocabulary and no lattice or global
frame.  A cluster prototype is centred at its (unweighted) centroid.  An
observed connection is represented in the parent cluster's local frame by

    child_point_in_parent = relative_rotation @ child_point + translation.

The recovered pose is quotiented by the proper rotational automorphisms of
both prototypes.  Thus two poses have one port identity exactly when they are
in the same double symmetry orbit

    (R, t) ~ (S_parent.T @ R @ S_child, S_parent.T @ t).

Only witnessed, species-preserving overlaps are compiled.  Reflections and
nearby unlike-species collisions are rejected.  Coordinates and species are
the complete input; energies, material labels, axes, and construction order
are absent from the contract.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import FrozenSet, Hashable, Iterable, Sequence, Tuple

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]
Site = Tuple[Hashable, Vector]

IDENTITY: Matrix = ((1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (0.0, 0.0, 1.0))


@dataclass(frozen=True)
class ClusterPrototype:
    type_id: int
    sites: Tuple[Site, ...]
    proper_symmetries: Tuple[Matrix, ...]


@dataclass(frozen=True)
class ClusterOccurrence:
    """A witnessed prototype pose, mapping local coordinates into the sample."""

    occurrence_id: int
    type_id: int
    rotation: Matrix
    translation: Vector


@dataclass(frozen=True)
class OrientedOverlapPort:
    parent_type: int
    child_type: int
    relative_rotation: Matrix
    relative_translation: Vector
    overlap: Tuple[Tuple[int, int], ...]
    overlap_species: Tuple[Hashable, ...]
    symmetry_orbit_key: Tuple[int, ...]
    observations: int


@dataclass(frozen=True)
class PortAtlas:
    ports: Tuple[OrientedOverlapPort, ...]
    witnessed_relations: int
    symmetry_orbit_collapses: int
    rejected_improper_occurrences: int
    rejected_conflicting_relations: int
    discarded_rare_classes: int
    relation_classes: Tuple[Tuple[int, int, int, int, Tuple[int, ...]], ...]


def _add(a: Vector, b: Vector) -> Vector:
    return tuple(a[i] + b[i] for i in range(3))  # type: ignore[return-value]


def _subtract(a: Vector, b: Vector) -> Vector:
    return tuple(a[i] - b[i] for i in range(3))  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(a[i] * b[i] for i in range(3))


def _cross(a: Vector, b: Vector) -> Vector:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a: Vector) -> float:
    return math.sqrt(_dot(a, a))


def _scale(factor: float, a: Vector) -> Vector:
    return tuple(factor * value for value in a)  # type: ignore[return-value]


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    return tuple(_dot(row, vector) for row in matrix)  # type: ignore[return-value]


def transpose(matrix: Matrix) -> Matrix:
    return tuple(tuple(matrix[column][row] for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def matmul(left: Matrix, right: Matrix) -> Matrix:
    return tuple(tuple(sum(left[row][axis] * right[axis][column]
                           for axis in range(3))
                       for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def determinant(matrix: Matrix) -> float:
    return _dot(matrix[0], _cross(matrix[1], matrix[2]))


def is_proper_rotation(matrix: Matrix, tolerance: float = 1e-7) -> bool:
    product = matmul(transpose(matrix), matrix)
    return (abs(determinant(matrix) - 1.0) <= tolerance and
            all(abs(product[row][column] - (1.0 if row == column else 0.0))
                <= tolerance for row in range(3) for column in range(3)))


def _frame(first: Vector, second: Vector) -> Matrix | None:
    length = _norm(first)
    if length <= 1e-10:
        return None
    x = _scale(1.0 / length, first)
    residual = _subtract(second, _scale(_dot(second, x), x))
    length = _norm(residual)
    if length <= 1e-10:
        return None
    y = _scale(1.0 / length, residual)
    z = _cross(x, y)
    # Frames are matrices with basis vectors as columns.
    return tuple(tuple((x, y, z)[column][row] for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _rotation(source: Matrix, target: Matrix) -> Matrix:
    return matmul(target, transpose(source))


def _quantized(values: Iterable[float], tolerance: float) -> Tuple[int, ...]:
    return tuple(round(value / tolerance) for value in values)


def _matrix_key(matrix: Matrix, tolerance: float) -> Tuple[int, ...]:
    return _quantized((value for row in matrix for value in row), tolerance)


def _pose_key(rotation: Matrix, translation: Vector,
              tolerance: float) -> Tuple[int, ...]:
    return (_matrix_key(rotation, tolerance) +
            _quantized(translation, tolerance))


def _match_colored_sets(source: Sequence[Site], target: Sequence[Site],
                        rotation: Matrix, tolerance: float) -> bool:
    unmatched = set(range(len(target)))
    for species, point in source:
        moved = matvec(rotation, point)
        candidates = [index for index in unmatched
                      if target[index][0] == species and
                      math.dist(moved, target[index][1]) <= tolerance]
        if not candidates:
            return False
        unmatched.remove(min(candidates,
                             key=lambda index: math.dist(
                                 moved, target[index][1])))
    return not unmatched


def proper_point_symmetries(sites: Sequence[Site],
                            tolerance: float = 1e-6) -> Tuple[Matrix, ...]:
    """Enumerate the finite proper rotation group of a centred colored set.

    A non-collinear ordered anchor pair fixes a unique proper rotation.  The
    first usable pair is sufficient: every automorphism must map that pair to
    a chemically and metrically compatible pair.  Collinear point sets have a
    continuous stabilizer and are rejected rather than discretized silently.
    """
    sites = tuple(sites)
    source_pair = None
    for first in range(len(sites)):
        for second in range(len(sites)):
            if first != second and _norm(_cross(
                    sites[first][1], sites[second][1])) > tolerance:
                source_pair = (first, second)
                break
        if source_pair is not None:
            break
    if source_pair is None:
        raise ValueError("cluster must contain a non-collinear centred pair")
    first, second = source_pair
    source_frame = _frame(sites[first][1], sites[second][1])
    assert source_frame is not None
    rotations = {}
    source_dot = _dot(sites[first][1], sites[second][1])
    for target_first in range(len(sites)):
        if (sites[target_first][0] != sites[first][0] or
                abs(_norm(sites[target_first][1]) -
                    _norm(sites[first][1])) > tolerance):
            continue
        for target_second in range(len(sites)):
            if (target_second == target_first or
                    sites[target_second][0] != sites[second][0] or
                    abs(_norm(sites[target_second][1]) -
                        _norm(sites[second][1])) > tolerance or
                    abs(_dot(sites[target_first][1], sites[target_second][1]) -
                        source_dot) > tolerance):
                continue
            target_frame = _frame(sites[target_first][1],
                                  sites[target_second][1])
            if target_frame is None:
                continue
            rotation = _rotation(source_frame, target_frame)
            if (is_proper_rotation(rotation) and
                    _match_colored_sets(sites, sites, rotation, tolerance)):
                rotations[_matrix_key(rotation, tolerance)] = rotation
    if not rotations:
        raise AssertionError("identity symmetry was not recovered")
    return tuple(rotations[key] for key in sorted(rotations))


def make_prototype(type_id: int, sites: Sequence[Site],
                   tolerance: float = 1e-6) -> ClusterPrototype:
    """Centre a finite colored cluster and learn all its proper symmetries."""
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    if len(sites) < 3:
        raise ValueError("a finite oriented cluster needs at least three sites")
    if any(not all(math.isfinite(value) for value in point)
           for _, point in sites):
        raise ValueError("cluster coordinates must be finite")
    if any(math.dist(sites[first][1], sites[second][1]) <= tolerance
           for first in range(len(sites))
           for second in range(first + 1, len(sites))):
        raise ValueError("cluster sites must obey the minimum-distance bound")
    centroid = tuple(sum(point[axis] for _, point in sites) / len(sites)
                     for axis in range(3))
    centered = tuple((species, _subtract(point, centroid))
                     for species, point in sites)
    return ClusterPrototype(
        type_id, centered, proper_point_symmetries(centered, tolerance))


def fit_occurrence_pose(
    occurrence_id: int, prototype: ClusterPrototype,
    observed_sites: Sequence[Site], tolerance: float = 1e-6,
) -> ClusterOccurrence:
    """Fit a proper local-to-world pose without a distinguished centre.

    The prototype and observation are unordered colored point sets. Their
    centroids fix translation; a chemically compatible non-collinear anchor
    pair fixes a candidate proper rotation. Reflected congruences therefore
    fail instead of entering the finite port atlas as rotations.
    """
    if len(observed_sites) != len(prototype.sites):
        raise ValueError("prototype and occurrence must have equal size")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    translation = tuple(
        sum(point[axis] for _, point in observed_sites) / len(observed_sites)
        for axis in range(3))
    centered = tuple((species, _subtract(point, translation))
                     for species, point in observed_sites)
    source_pair = next((
        (first, second)
        for first in range(len(prototype.sites))
        for second in range(len(prototype.sites))
        if first != second and _norm(_cross(
            prototype.sites[first][1], prototype.sites[second][1])) > tolerance
    ), None)
    if source_pair is None:
        raise ValueError("prototype needs a non-collinear anchor pair")
    first, second = source_pair
    source_frame = _frame(prototype.sites[first][1],
                          prototype.sites[second][1])
    assert source_frame is not None
    source_dot = _dot(prototype.sites[first][1],
                      prototype.sites[second][1])
    for target_first in range(len(centered)):
        if (centered[target_first][0] != prototype.sites[first][0] or
                abs(_norm(centered[target_first][1]) -
                    _norm(prototype.sites[first][1])) > tolerance):
            continue
        for target_second in range(len(centered)):
            if (target_second == target_first or
                    centered[target_second][0] != prototype.sites[second][0] or
                    abs(_norm(centered[target_second][1]) -
                        _norm(prototype.sites[second][1])) > tolerance or
                    abs(_dot(centered[target_first][1],
                             centered[target_second][1]) - source_dot) > tolerance):
                continue
            target_frame = _frame(centered[target_first][1],
                                  centered[target_second][1])
            if target_frame is None:
                continue
            rotation = _rotation(source_frame, target_frame)
            if (is_proper_rotation(rotation) and _match_colored_sets(
                    prototype.sites, centered, rotation, tolerance)):
                return ClusterOccurrence(
                    occurrence_id, prototype.type_id, rotation, translation)
    raise ValueError("observed colored set is not a proper rigid occurrence")


def canonical_relative_pose(
    parent: ClusterPrototype, child: ClusterPrototype,
    rotation: Matrix, translation: Vector, tolerance: float = 1e-6,
) -> Tuple[Matrix, Vector, Tuple[int, ...]]:
    """Return the minimum key in the parent/child proper-symmetry orbit."""
    if not is_proper_rotation(rotation):
        raise ValueError("relative pose is not a proper rotation")
    candidates = []
    for parent_symmetry in parent.proper_symmetries:
        inverse_parent = transpose(parent_symmetry)
        shifted = matvec(inverse_parent, translation)
        for child_symmetry in child.proper_symmetries:
            rotated = matmul(
                matmul(inverse_parent, rotation), child_symmetry)
            candidates.append((_pose_key(rotated, shifted, tolerance),
                               rotated, shifted))
    key, canonical_rotation, canonical_translation = min(candidates,
                                                          key=lambda x: x[0])
    return canonical_rotation, canonical_translation, key


def _overlap(
    parent: ClusterPrototype, child: ClusterPrototype,
    rotation: Matrix, translation: Vector, overlap_tolerance: float,
    exclusion_distance: float,
) -> Tuple[Tuple[Tuple[int, int], ...], bool]:
    pairs = []
    conflicting = False
    moved = tuple(_add(matvec(rotation, point), translation)
                  for _, point in child.sites)
    for parent_index, (parent_species, parent_point) in enumerate(parent.sites):
        for child_index, ((child_species, _), child_point) in enumerate(
                zip(child.sites, moved)):
            distance = math.dist(parent_point, child_point)
            if distance <= overlap_tolerance:
                if parent_species != child_species:
                    conflicting = True
                else:
                    pairs.append((parent_index, child_index))
            elif distance < exclusion_distance:
                conflicting = True
    return tuple(sorted(pairs)), conflicting


def learn_overlap_ports(
    prototypes: Sequence[ClusterPrototype],
    occurrences: Sequence[ClusterOccurrence],
    *,
    minimum_overlap: int = 1,
    minimum_observations: int = 1,
    overlap_tolerance: float = 1e-6,
    exclusion_distance: float = 1e-3,
    allowed_type_pairs: FrozenSet[Tuple[int, int]] | None = None,
    allowed_occurrence_pairs: FrozenSet[Tuple[int, int]] | None = None,
) -> PortAtlas:
    """Compile a finite atlas from witnessed ordered cluster connections."""
    if minimum_overlap < 1 or minimum_observations < 1:
        raise ValueError("minimum overlap and observations must be positive")
    if overlap_tolerance <= 0 or exclusion_distance < overlap_tolerance:
        raise ValueError(
            "exclusion_distance must be at least the positive overlap tolerance")
    by_type = {prototype.type_id: prototype for prototype in prototypes}
    if len(by_type) != len(prototypes):
        raise ValueError("prototype type ids must be unique")
    occurrence_ids = {occurrence.occurrence_id for occurrence in occurrences}
    if len(occurrence_ids) != len(occurrences):
        raise ValueError("occurrence ids must be unique")
    if (allowed_occurrence_pairs is not None and any(
            left not in occurrence_ids or right not in occurrence_ids
            for left, right in allowed_occurrence_pairs)):
        raise ValueError("allowed occurrence pair uses an unknown id")
    valid = []
    rejected_improper = 0
    for occurrence in occurrences:
        if occurrence.type_id not in by_type:
            raise ValueError(f"unknown cluster type {occurrence.type_id}")
        if not is_proper_rotation(occurrence.rotation):
            rejected_improper += 1
            continue
        valid.append(occurrence)
    aggregates = {}
    relation_classes = []
    witnessed = rejected_conflicts = 0
    for parent_occurrence in valid:
        for child_occurrence in valid:
            if parent_occurrence.occurrence_id == child_occurrence.occurrence_id:
                continue
            if (allowed_occurrence_pairs is not None and
                    (parent_occurrence.occurrence_id,
                     child_occurrence.occurrence_id) not in
                    allowed_occurrence_pairs):
                continue
            type_pair = (parent_occurrence.type_id, child_occurrence.type_id)
            if allowed_type_pairs is not None and type_pair not in allowed_type_pairs:
                continue
            parent = by_type[parent_occurrence.type_id]
            child = by_type[child_occurrence.type_id]
            inverse_parent = transpose(parent_occurrence.rotation)
            relative_rotation = matmul(inverse_parent,
                                      child_occurrence.rotation)
            relative_translation = matvec(inverse_parent, _subtract(
                child_occurrence.translation,
                parent_occurrence.translation))
            canonical_rotation, canonical_translation, pose_key = (
                canonical_relative_pose(parent, child, relative_rotation,
                                        relative_translation,
                                        overlap_tolerance))
            overlap, conflict = _overlap(
                parent, child, canonical_rotation, canonical_translation,
                overlap_tolerance, exclusion_distance)
            if conflict:
                rejected_conflicts += 1
                continue
            if len(overlap) < minimum_overlap:
                continue
            witnessed += 1
            key = type_pair + (pose_key,)
            relation_classes.append((
                parent_occurrence.occurrence_id,
                child_occurrence.occurrence_id,
                parent_occurrence.type_id, child_occurrence.type_id,
                pose_key))
            if key not in aggregates:
                aggregates[key] = [canonical_rotation,
                                   canonical_translation, overlap, 0]
            aggregates[key][3] += 1
    ports = []
    discarded_rare = 0
    for key in sorted(aggregates, key=repr):
        rotation, translation, overlap, observations = aggregates[key]
        if observations < minimum_observations:
            discarded_rare += 1
            continue
        parent_type, child_type = key[:2]
        parent = by_type[parent_type]
        species = tuple(parent.sites[parent_index][0]
                        for parent_index, _ in overlap)
        ports.append(OrientedOverlapPort(
            parent_type, child_type, rotation, translation, overlap,
            species, key[2], observations))
    return PortAtlas(
        tuple(ports), witnessed, witnessed - len(aggregates),
        rejected_improper, rejected_conflicts, discarded_rare,
        tuple(relation_classes))


def place_child(parent_rotation: Matrix, parent_translation: Vector,
                port: OrientedOverlapPort) -> Tuple[Matrix, Vector]:
    """Compose a port with a parent occurrence using standard SE(3)."""
    rotation = matmul(parent_rotation, port.relative_rotation)
    translation = _add(
        parent_translation,
        matvec(parent_rotation, port.relative_translation))
    return rotation, translation


def expand_port_orbit(
    parent: ClusterPrototype, child: ClusterPrototype,
    port: OrientedOverlapPort, tolerance: float = 1e-6,
) -> Tuple[Tuple[Matrix, Vector], ...]:
    """Recover all distinct physical attachments represented by one port.

    Canonicalization intentionally folds symmetry-equivalent directions into
    one finite port class. Search must unfold that class at a concrete parent.
    Child-gauge rotations that render the same colored site set are deduped,
    so an octahedral nearest-neighbor port expands to six placements, not
    24x24 matrix gauges.
    """
    if (port.parent_type != parent.type_id or
            port.child_type != child.type_id):
        raise ValueError("port types do not match the supplied prototypes")
    rendered = {}
    for parent_symmetry in parent.proper_symmetries:
        translation = matvec(parent_symmetry, port.relative_translation)
        for child_symmetry in child.proper_symmetries:
            rotation = matmul(
                matmul(parent_symmetry, port.relative_rotation),
                transpose(child_symmetry))
            sites = tuple(sorted(
                (repr(species),) + _quantized(
                    _add(matvec(rotation, point), translation), tolerance)
                for species, point in child.sites))
            key = sites
            rendered.setdefault(key, (rotation, translation))
    return tuple(rendered[key] for key in sorted(rendered))
