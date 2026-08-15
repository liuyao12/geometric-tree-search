#!/usr/bin/env python3
"""Adapt real learned macro atlases to stationary production semantics.

Raw atlas orbit keys contain quantized translations and therefore cannot be
stationary labels.  This adapter resolves each key back to its admitted finite
oriented port, replaces site indices with colored metric roles, retains proper
relative rotation, and divides relative translation by a scale measured from
the macro's child placements.  It reads no family, cell, target, potential, or
prescribed hierarchy scale.
"""

from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass
from typing import Any, Hashable, Sequence

from materials_gcts_oriented_overlap_ports import (
    ClusterPrototype, Matrix, OrientedOverlapPort, Vector, matvec, transpose)
from materials_gcts_stationary_production_signature import (
    CanonicalProduction, PortGraphProduction, canonicalize_production,
    production_from_macro_type)


@dataclass(frozen=True)
class PrototypeSemantics:
    chemistry_key: tuple[str, ...]
    chemical_population: tuple[tuple[str, int], ...]
    chirality_key: str
    characteristic_scale: float
    proper_symmetries: tuple[Matrix, ...]


@dataclass(frozen=True)
class AdaptedMacroProduction:
    production: PortGraphProduction
    canonical: CanonicalProduction
    resolved_port_classes: int
    child_prototype_types: int
    child_chemical_populations: tuple[tuple[tuple[str, int], ...], ...]
    family_label_used: bool
    lattice_or_cell_used: bool
    physical_potential_used: bool
    target_used: bool
    prescribed_scale_used: bool

    @property
    def leakage_clean(self) -> bool:
        return not any((self.family_label_used, self.lattice_or_cell_used,
                        self.physical_potential_used, self.target_used,
                        self.prescribed_scale_used))


def _subtract(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(left[index] - right[index] for index in range(3))  # type: ignore[return-value]


def _scale(value: float, point: Sequence[float]) -> Vector:
    return tuple(value * coordinate for coordinate in point)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(left[index] * right[index] for index in range(3))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _norm(point: Sequence[float]) -> float:
    return math.sqrt(_dot(point, point))


def _frame(first: Vector, second: Vector,
           tolerance: float) -> Matrix | None:
    length = _norm(first)
    if length <= tolerance:
        return None
    x = _scale(1.0 / length, first)
    residual = _subtract(second, _scale(_dot(second, x), x))
    length = _norm(residual)
    if length <= tolerance:
        return None
    y = _scale(1.0 / length, residual)
    z = _cross(x, y)
    return tuple(tuple((x, y, z)[column][row] for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _quantized(values: Sequence[float], tolerance: float) -> tuple[int, ...]:
    return tuple(round(value / tolerance) for value in values)


def _matrix_key(matrix: Matrix, tolerance: float) -> tuple[int, ...]:
    return _quantized(tuple(value for row in matrix for value in row),
                      tolerance)


def _species(value: Hashable) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}:{value!r}"


def _chemistry(labels: Sequence[str]) -> tuple[
        tuple[str, ...], tuple[tuple[str, int], ...]]:
    population = tuple(sorted((label, labels.count(label))
                              for label in set(labels)))
    divisor = 0
    for _, count in population:
        divisor = math.gcd(divisor, count)
    reduced = tuple(f"{label}*{count // divisor}"
                    for label, count in population)
    return reduced, population


def _proper_geometry_code(sites, scale: float, tolerance: float):
    fingerprints = tuple((species, tuple(sorted(
        (other_species, round(math.dist(point, other_point) /
                              scale / tolerance))
        for other, (other_species, other_point) in enumerate(sites)
        if other != index)))
        for index, (species, point) in enumerate(sites))
    fingerprint_rank = {value: rank for rank, value in
                        enumerate(sorted(set(fingerprints)))}
    best_invariant = None
    anchors = []
    for first, second, third in itertools.permutations(range(len(sites)), 3):
        origin = sites[first][1]
        first_vector = _subtract(sites[second][1], origin)
        second_vector = _subtract(sites[third][1], origin)
        if _norm(_cross(first_vector, second_vector)) <= tolerance * scale:
            continue
        invariant = (
            fingerprint_rank[fingerprints[first]],
            fingerprint_rank[fingerprints[second]],
            fingerprint_rank[fingerprints[third]],
            round(math.dist(sites[first][1], sites[second][1]) /
                  scale / tolerance),
            round(math.dist(sites[first][1], sites[third][1]) /
                  scale / tolerance),
            round(math.dist(sites[second][1], sites[third][1]) /
                  scale / tolerance))
        if best_invariant is None or invariant < best_invariant:
            best_invariant = invariant
            anchors = [(first, second, third)]
        elif invariant == best_invariant:
            anchors.append((first, second, third))
    alternatives = []
    for first, second, third in anchors:
        origin = sites[first][1]
        frame = _frame(_subtract(sites[second][1], origin),
                       _subtract(sites[third][1], origin), tolerance * scale)
        assert frame is not None
        inverse = transpose(frame)
        alternatives.append(tuple(sorted((species,) + _quantized(
            _scale(1.0 / scale,
                   matvec(inverse, _subtract(point, origin))), tolerance)
                                         for species, point in sites)))
    if not alternatives:
        raise ValueError("prototype needs a non-collinear proper frame")
    return min(alternatives)


def prototype_semantics(
        prototype: ClusterPrototype, *,
        tolerance: float = 1e-6) -> PrototypeSemantics:
    """Return exact chemistry and a scale-free proper-geometry signature."""
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    sites = tuple((_species(species), point)
                  for species, point in prototype.sites)
    chemistry, population = _chemistry(
        tuple(species for species, _ in sites))
    distances = tuple(math.dist(left[1], right[1])
                      for index, left in enumerate(sites)
                      for right in sites[index + 1:])
    positive = tuple(distance for distance in distances
                     if distance > tolerance)
    if not positive:
        raise ValueError("prototype needs separated sites")
    scale = min(positive)
    proper = _proper_geometry_code(sites, scale, tolerance)
    mirrored_sites = tuple((species, (-point[0], point[1], point[2]))
                           for species, point in sites)
    mirrored = _proper_geometry_code(mirrored_sites, scale, tolerance)
    chirality = ("achiral" if proper == mirrored else
                 ("chiral-A" if proper < mirrored else "chiral-B"))
    return PrototypeSemantics(
        chemistry, population, chirality, scale,
        prototype.proper_symmetries)


def _macro_scale(macro: Any, tolerance: float) -> float:
    translations = tuple(item.translation for item in macro.child_placements)
    positive = tuple(math.dist(left, right)
                     for index, left in enumerate(translations)
                     for right in translations[index + 1:]
                     if math.dist(left, right) > tolerance)
    if not positive:
        raise ValueError("macro needs separated child placements")
    return min(positive)


def adapt_macro_type(
        artifact: Any, macro: Any, *, tolerance: float = 1e-6,
        prototype_semantics_cache: dict[int, PrototypeSemantics] | None = None,
) -> AdaptedMacroProduction:
    """Resolve one real ``MacroType`` to canonical stationary semantics."""
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    prototypes = {prototype.type_id: prototype
                  for prototype in artifact.prototypes}
    if len(prototypes) != len(artifact.prototypes):
        raise ValueError("artifact prototype ids must be unique")
    child_types = {item.cluster_type for item in macro.child_placements}
    outside_types = {slot.outside_type for slot in macro.boundary_slots}
    requested_types = child_types | outside_types
    if not requested_types.issubset(prototypes):
        raise ValueError("macro references an unknown prototype")
    semantics = (prototype_semantics_cache
                 if prototype_semantics_cache is not None else {})
    for type_id in requested_types:
        if type_id not in semantics:
            semantics[type_id] = prototype_semantics(
                prototypes[type_id], tolerance=tolerance)
    port_lookup = {
        (port.parent_type, port.child_type, port.symmetry_orbit_key): port
        for port in artifact.atlas.ports}
    if len(port_lookup) != len(artifact.atlas.ports):
        raise ValueError("atlas contains duplicate admitted port ids")
    scale = _macro_scale(macro, tolerance)
    resolved = set()

    def port_semantics(raw):
        raw = tuple(raw)
        if raw not in port_lookup:
            raise ValueError("macro port is not admitted by the source atlas")
        port: OrientedOverlapPort = port_lookup[raw]
        parent = prototypes[port.parent_type]
        child = prototypes[port.child_type]
        for type_id, prototype in ((port.parent_type, parent),
                                   (port.child_type, child)):
            if type_id not in semantics:
                semantics[type_id] = prototype_semantics(
                    prototype, tolerance=tolerance)
        overlap, _ = _chemistry(tuple(
            _species(species) for species in port.overlap_species)) \
            if port.overlap_species else ((), ())
        key = (
            "colored-overlap",
            "overlap:" + json.dumps(overlap, separators=(",", ":")),
            "proper-R:" + ",".join(map(str, _matrix_key(
                port.relative_rotation, tolerance))),
            "scaled-t:" + ",".join(map(str, _quantized(
                _scale(1.0 / scale, port.relative_translation), tolerance))),
        )
        resolved.add(raw)
        return key, overlap

    production = production_from_macro_type(
        macro,
        chemistry_by_cluster_type={key: value.chemistry_key
                                   for key, value in semantics.items()},
        chirality_by_cluster_type={key: value.chirality_key
                                   for key, value in semantics.items()},
        symmetries_by_cluster_type={key: value.proper_symmetries
                                    for key, value in semantics.items()},
        port_semantics=port_semantics,
        outside_chemistry=lambda type_id: semantics[type_id].chemistry_key,
        population_by_cluster_type={
            key: value.chemical_population
            for key, value in semantics.items()})
    canonical = canonicalize_production(production, tolerance=tolerance)
    populations = tuple(semantics[item.cluster_type].chemical_population
                        for item in sorted(macro.child_placements,
                                           key=lambda child: child.node))
    return AdaptedMacroProduction(
        production, canonical, len(resolved), len(child_types), populations,
        bool(getattr(artifact, "family_label_used", False)),
        bool(getattr(artifact, "lattice_used", False) or
             getattr(artifact, "cell_used", False)),
        bool(getattr(artifact, "physical_potential_used", False)),
        bool(getattr(artifact, "target_used", False)), False)
