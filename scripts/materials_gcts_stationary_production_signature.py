#!/usr/bin/env python3
"""Canonical stationary signatures for recurring port-graph productions.

The equivalence relation is intentionally narrow.  It removes global proper
SE(3), input child order, declared *proper* child gauges, and one uniform
positive scale on relative translations.  It does not remove chemistry,
chirality, directed port incidence, overlap chemistry, or boundary slots.

One scale comparison is not stationary evidence.  ``stationary_evidence``
requires the same normalized production at l, l+1 and l+2, equal learned
scale on both adjacent comparisons, independent recurring occurrences, and a
positive description-length saving at every observed level.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from materials_gcts_oriented_overlap_ports import (
    IDENTITY, Matrix, Vector, is_proper_rotation, matmul, matvec, transpose)


@dataclass(frozen=True)
class ProductionChild:
    chemistry_key: tuple[str, ...]
    chirality_key: str
    rotation: Matrix
    translation: Vector
    proper_symmetries: tuple[Matrix, ...] = (IDENTITY,)
    chemical_population: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class ProductionPort:
    source: int
    target: int
    port_key: tuple[str, ...]
    overlap_chemistry: tuple[str, ...]


@dataclass(frozen=True)
class ProductionBoundary:
    child: int
    direction: str
    outside_chemistry_key: tuple[str, ...]
    port_key: tuple[str, ...]
    overlap_chemistry: tuple[str, ...]


@dataclass(frozen=True)
class PortGraphProduction:
    children: tuple[ProductionChild, ...]
    internal_ports: tuple[ProductionPort, ...]
    boundary_slots: tuple[ProductionBoundary, ...] = ()


@dataclass(frozen=True)
class CanonicalProduction:
    normalized_key: str
    normalized_code: tuple
    intrinsic_translation_scale: float
    canonical_original_order: tuple[int, ...]
    normalized_translations: tuple[Vector, ...]
    gauged_rotations: tuple[Matrix, ...]


@dataclass(frozen=True)
class StationaryComparison:
    stationary: bool
    normalized_key_equal: bool
    learned_similarity_scale: float | None
    maximum_normalized_translation_residual: float
    maximum_rotation_residual: float
    reason: str
    chemical_population_audit: "ChemicalPopulationAudit | None" = None


@dataclass(frozen=True)
class ChemicalPopulationAudit:
    checked: bool
    consistent: bool
    species: tuple[str, ...]
    role_keys: tuple[tuple[tuple[str, ...], str], ...]
    substitution_matrix: tuple[tuple[int, ...], ...]
    expanding: bool
    reason: str


@dataclass(frozen=True)
class PromotionObservation:
    hierarchy_level: int
    production: PortGraphProduction
    independent_occurrences: int
    maximum_occurrence_atom_overlap_fraction: float
    mdl_saving: int
    learned_from_training_only: bool = True


@dataclass(frozen=True)
class StationaryProductionEvidence:
    stationary: bool
    observed_levels: tuple[int, ...]
    normalized_production_key: str
    learned_similarity_scale: float | None
    adjacent_comparisons: tuple[StationaryComparison, ...]
    reason: str


def _subtract(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(left[index] - right[index] for index in range(3))  # type: ignore[return-value]


def _scale(value: float, vector: Sequence[float]) -> Vector:
    return tuple(value * coordinate for coordinate in vector)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(left[index] * right[index] for index in range(3))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _frame(first: Vector, second: Vector, tolerance: float) -> Matrix | None:
    first_length = _norm(first)
    if first_length <= tolerance:
        return None
    x = _scale(1.0 / first_length, first)
    residual = _subtract(second, _scale(_dot(second, x), x))
    second_length = _norm(residual)
    if second_length <= tolerance:
        return None
    y = _scale(1.0 / second_length, residual)
    z = _cross(x, y)
    # Basis vectors are columns; x cross y fixes a proper frame.
    return tuple(tuple((x, y, z)[column][row] for column in range(3))
                 for row in range(3))  # type: ignore[return-value]


def _matrix_residual(left: Matrix, right: Matrix) -> float:
    return max(abs(left[row][column] - right[row][column])
               for row in range(3) for column in range(3))


def _quantized(values: Sequence[float], tolerance: float) -> tuple[int, ...]:
    return tuple(round(value / tolerance) for value in values)


def _matrix_key(matrix: Matrix, tolerance: float) -> tuple[int, ...]:
    return _quantized(tuple(value for row in matrix for value in row),
                      tolerance)


def _validate(production: PortGraphProduction, tolerance: float) -> float:
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    # The canonicalizer is non-factorial in the ordinary case, so the strong
    # contract can cover train-inferred higher-radix 3-D subdivisions (for
    # example 27 children) without prescribing octuplication. The finite cap is
    # a denial-of-service guard, not a semantic production prior.
    if not 3 <= len(production.children) <= 64:
        raise ValueError("a stationary production needs 3--64 child macros")
    if any(not child.chemistry_key or not child.chirality_key
           for child in production.children):
        raise ValueError("every child needs chemistry and chirality keys")
    if any(not is_proper_rotation(child.rotation, tolerance * 10) or
           not child.proper_symmetries or
           any(not is_proper_rotation(symmetry, tolerance * 10)
               for symmetry in child.proper_symmetries)
           for child in production.children):
        raise ValueError("child poses and gauges must be proper rotations")
    count = len(production.children)
    if any(port.source == port.target or not 0 <= port.source < count or
           not 0 <= port.target < count or not port.port_key
           for port in production.internal_ports):
        raise ValueError("invalid directed internal port")
    if any(not 0 <= slot.child < count or
           slot.direction not in ("incoming", "outgoing") or
           not slot.outside_chemistry_key or not slot.port_key
           for slot in production.boundary_slots):
        raise ValueError("invalid boundary slot")
    # An arbitrary copied point patch without a connected witnessed port graph
    # is not a graph production.
    adjacency = {index: set() for index in range(count)}
    for port in production.internal_ports:
        adjacency[port.source].add(port.target)
        adjacency[port.target].add(port.source)
    reached = {0}
    pending = [0]
    while pending:
        node = pending.pop()
        for neighbor in adjacency[node] - reached:
            reached.add(neighbor)
            pending.append(neighbor)
    if len(reached) != count:
        raise ValueError("internal port incidence must weakly connect all children")
    distances = tuple(math.dist(left.translation, right.translation)
                      for index, left in enumerate(production.children)
                      for right in production.children[index + 1:])
    positive = tuple(distance for distance in distances
                     if distance > tolerance)
    if len(positive) != len(distances):
        raise ValueError("child macro translations must be distinct")
    scale = min(positive)
    points = tuple(child.translation for child in production.children)
    if not any(_norm(_cross(_subtract(points[j], points[i]),
                            _subtract(points[k], points[i]))) >
               tolerance * scale
               for i, j, k in itertools.permutations(range(count), 3)):
        raise ValueError("child translations must contain a non-collinear triple")
    return scale


def canonicalize_production(
        production: PortGraphProduction, *,
        tolerance: float = 1e-6) -> CanonicalProduction:
    """Canonicalize modulo proper world pose, child order/gauge, and scale."""
    scale = _validate(production, tolerance)
    count = len(production.children)
    points = tuple(child.translation for child in production.children)
    distances = tuple(tuple(math.dist(left, right) for right in points)
                      for left in points)
    # Select intrinsic anchor triples by an invariant colored-distance record
    # before rendering full productions. This retains exact canonical semantics
    # but avoids O(n^4) work for higher-radix grid productions.
    fingerprints = tuple((
        production.children[index].chemistry_key,
        production.children[index].chirality_key,
        tuple(sorted((
            production.children[other].chemistry_key,
            production.children[other].chirality_key,
            round(distances[index][other] / scale / tolerance))
            for other in range(count) if other != index)))
        for index in range(count))
    anchor_key = None
    anchors = []
    for first, second, third in itertools.permutations(range(count), 3):
        first_vector = _subtract(points[second], points[first])
        second_vector = _subtract(points[third], points[first])
        area = _norm(_cross(first_vector, second_vector))
        if _frame(first_vector, second_vector, tolerance * scale) is None:
            continue
        invariant = (
            fingerprints[first], fingerprints[second], fingerprints[third],
            round(distances[first][second] / scale / tolerance),
            round(distances[first][third] / scale / tolerance),
            round(distances[second][third] / scale / tolerance),
            round(area / (scale * scale) / tolerance))
        if anchor_key is None or invariant < anchor_key:
            anchor_key, anchors = invariant, [(first, second, third)]
        elif invariant == anchor_key:
            anchors.append((first, second, third))
    alternatives = []
    for first, second, third in anchors:
        origin = production.children[first].translation
        frame = _frame(
            _subtract(production.children[second].translation, origin),
            _subtract(production.children[third].translation, origin),
            tolerance * scale)
        if frame is None:
            continue
        inverse = transpose(frame)
        transformed = []
        for original, child in enumerate(production.children):
            translation = _scale(
                1.0 / scale,
                matvec(inverse, _subtract(child.translation, origin)))
            rotation_options = tuple(
                matmul(matmul(inverse, child.rotation), symmetry)
                for symmetry in child.proper_symmetries)
            rotation = min(rotation_options,
                           key=lambda item: _matrix_key(item, tolerance))
            transformed.append((original, translation, rotation))
        # Transformed positions are distinct by validation, so the complete
        # child record gives a deterministic order.  Enumerating n! arbitrary
        # input orders is unnecessary and makes natural 3D octuplication
        # needlessly expensive.
        records = tuple((
                production.children[original].chemistry_key,
                production.children[original].chirality_key,
                _quantized(transformed[original][1], tolerance),
                _matrix_key(transformed[original][2], tolerance),
                original) for original in range(count))
        tied: dict[tuple, list[int]] = {}
        for *record, original in records:
            tied.setdefault(tuple(record), []).append(original)
        groups = tuple((key, tuple(values)) for key, values in
                       sorted(tied.items()))
        # Float-distinct children can occasionally land in the same tolerance
        # bin. Enumerate only those tied groups; using raw input index as a
        # tiebreak would leak child order into directed incidence.
        for tied_orders in itertools.product(*(
                tuple(itertools.permutations(values))
                for _, values in groups)):
            order = tuple(original for group in tied_orders
                          for original in group)
            original_to_new = {original: new
                               for new, original in enumerate(order)}
            children_code = tuple(key for key, values in groups
                                  for _ in values)
            ports_code = tuple(sorted((
                original_to_new[port.source], original_to_new[port.target],
                port.port_key, port.overlap_chemistry)
                for port in production.internal_ports))
            boundary_code = tuple(sorted((
                original_to_new[slot.child], slot.direction,
                slot.outside_chemistry_key, slot.port_key,
                slot.overlap_chemistry)
                for slot in production.boundary_slots))
            code = children_code, ports_code, boundary_code
            alternatives.append((
                code, order,
                tuple(transformed[original][1] for original in order),
                tuple(transformed[original][2] for original in order)))
    if not alternatives:
        raise ValueError("no proper intrinsic production frame exists")
    code, order, translations, rotations = min(
        alternatives, key=lambda item: item[0])
    payload = json.dumps(code, separators=(",", ":"), ensure_ascii=True)
    key = hashlib.sha256(payload.encode()).hexdigest()
    return CanonicalProduction(
        key, code, scale, tuple(order), tuple(translations), tuple(rotations))


def _population_by_role(production: PortGraphProduction):
    grouped = {}
    any_population = False
    for child in production.children:
        role = child.chemistry_key, child.chirality_key
        population = tuple(sorted(child.chemical_population))
        if population:
            any_population = True
            if (any(count <= 0 for _, count in population) or
                    len({species for species, _ in population}) !=
                    len(population)):
                raise ValueError("chemical populations need unique positive counts")
        if role in grouped and grouped[role] != population:
            raise ValueError("one child role has inconsistent populations")
        grouped[role] = population
    return any_population, grouped


def _nonnegative_combination(vectors, target):
    if not vectors:
        return None
    dimensions = len(target)
    maximum = max(target, default=0)
    bounds = []
    for vector in vectors:
        positive = [value for value in vector if value > 0]
        bounds.append(maximum // min(positive) if positive else 0)
    def search(index, remaining):
        cache_key = index, remaining
        if cache_key in memo:
            return memo[cache_key]
        if index == len(vectors):
            result = () if not any(remaining) else None
            memo[cache_key] = result
            return result
        vector = vectors[index]
        bound = bounds[index]
        for dimension, value in enumerate(vector):
            if value:
                bound = min(bound, remaining[dimension] // value)
        # Deterministic lexicographic nonnegative solution.
        for coefficient in range(bound + 1):
            next_remaining = tuple(
                remaining[dimension] - coefficient * vector[dimension]
                for dimension in range(dimensions))
            if any(value < 0 for value in next_remaining):
                continue
            suffix = search(index + 1, next_remaining)
            if suffix is not None:
                result = (coefficient,) + suffix
                memo[cache_key] = result
                return result
        memo[cache_key] = None
        return None

    memo = {}
    return search(0, tuple(target))


def audit_chemical_population_substitution(
        lower: PortGraphProduction,
        upper: PortGraphProduction) -> ChemicalPopulationAudit:
    """Infer an exact nonnegative integer child-role substitution matrix."""
    try:
        lower_present, lower_by_role = _population_by_role(lower)
        upper_present, upper_by_role = _population_by_role(upper)
    except ValueError as error:
        return ChemicalPopulationAudit(
            True, False, (), (), (), False, str(error))
    if not lower_present and not upper_present:
        return ChemicalPopulationAudit(
            False, True, (), (), (), False,
            "chemical populations were not supplied")
    if not lower_present or not upper_present:
        return ChemicalPopulationAudit(
            True, False, (), (), (), False,
            "chemical populations are missing at one level")
    roles = tuple(sorted(lower_by_role))
    if roles != tuple(sorted(upper_by_role)):
        return ChemicalPopulationAudit(
            True, False, (), roles, (), False,
            "child-role vocabulary changes between levels")
    species = tuple(sorted({species for population in
                            tuple(lower_by_role.values()) +
                            tuple(upper_by_role.values())
                            for species, _ in population}))

    def vector(population):
        values = dict(population)
        return tuple(values.get(label, 0) for label in species)

    lower_vectors = tuple(vector(lower_by_role[role]) for role in roles)
    upper_vectors = tuple(vector(upper_by_role[role]) for role in roles)
    rows = []
    for target in upper_vectors:
        row = _nonnegative_combination(lower_vectors, target)
        if row is None:
            return ChemicalPopulationAudit(
                True, False, species, roles, (), False,
                "no exact nonnegative integer substitution exists")
        rows.append(row)
    lower_total = sum(map(sum, lower_vectors))
    upper_total = sum(map(sum, upper_vectors))
    expanding = upper_total > lower_total and any(
        sum(row) > 1 for row in rows)
    return ChemicalPopulationAudit(
        True, expanding, species, roles, tuple(rows), expanding,
        "" if expanding else "population substitution is not expanding")


def compare_stationary_productions(
        lower: PortGraphProduction, upper: PortGraphProduction, *,
        tolerance: float = 1e-6) -> StationaryComparison:
    """Compare two levels and infer their sole admissible uniform scale."""
    try:
        left = canonicalize_production(lower, tolerance=tolerance)
        right = canonicalize_production(upper, tolerance=tolerance)
    except ValueError as error:
        return StationaryComparison(
            False, False, None, math.inf, math.inf, str(error), None)
    equal = left.normalized_key == right.normalized_key
    translation_residual = max(
        math.dist(a, b) for a, b in zip(
            left.normalized_translations, right.normalized_translations))
    rotation_residual = max(
        _matrix_residual(a, b) for a, b in zip(
            left.gauged_rotations, right.gauged_rotations))
    learned_scale = (right.intrinsic_translation_scale /
                     left.intrinsic_translation_scale)
    population = audit_chemical_population_substitution(lower, upper)
    stationary = (equal and learned_scale > 1.0 and
                  translation_residual <= tolerance and
                  rotation_residual <= tolerance and population.consistent)
    reason = "" if stationary else (
        "normalized chemistry/chirality/port geometry differs" if not equal
        else population.reason if not population.consistent
        else "scale is not expanding or residual exceeds tolerance")
    return StationaryComparison(
        stationary, equal, learned_scale, translation_residual,
        rotation_residual, reason, population)


def stationary_evidence(
        observations: Sequence[PromotionObservation], *,
        tolerance: float = 1e-6,
        maximum_evidence_overlap_fraction: float = .1,
) -> StationaryProductionEvidence:
    """Require two equal adjacent comparisons across three train levels."""
    ordered = tuple(sorted(observations,
                           key=lambda item: item.hierarchy_level))
    levels = tuple(item.hierarchy_level for item in ordered)
    if len(ordered) < 3:
        return StationaryProductionEvidence(
            False, levels, "", None, (),
            "one scale comparison is not stationary evidence")
    evidence = tuple(item for item in ordered
                     if item.independent_occurrences >= 2 and
                     item.maximum_occurrence_atom_overlap_fraction <=
                     maximum_evidence_overlap_fraction and
                     item.mdl_saving > 0 and item.learned_from_training_only)
    for left, middle, right in zip(evidence, evidence[1:], evidence[2:]):
        if (middle.hierarchy_level != left.hierarchy_level + 1 or
                right.hierarchy_level != middle.hierarchy_level + 1):
            continue
        first = compare_stationary_productions(
            left.production, middle.production, tolerance=tolerance)
        second = compare_stationary_productions(
            middle.production, right.production, tolerance=tolerance)
        same_substitution = (
            first.chemical_population_audit is not None and
            second.chemical_population_audit is not None and
            (not first.chemical_population_audit.checked and
             not second.chemical_population_audit.checked or
             first.chemical_population_audit.substitution_matrix ==
             second.chemical_population_audit.substitution_matrix))
        if (first.stationary and second.stationary and same_substitution and
                math.isclose(first.learned_similarity_scale,
                             second.learned_similarity_scale,
                             rel_tol=tolerance, abs_tol=tolerance)):
            canonical = canonicalize_production(
                left.production, tolerance=tolerance)
            return StationaryProductionEvidence(
                True, (left.hierarchy_level, middle.hierarchy_level,
                       right.hierarchy_level), canonical.normalized_key,
                first.learned_similarity_scale, (first, second), "")
    return StationaryProductionEvidence(
        False, levels, "", None, (),
        "no three consecutive independent train levels share one production and scale")


def production_from_macro_type(
        macro: Any, *,
        chemistry_by_cluster_type: Mapping[int, tuple[str, ...]],
        chirality_by_cluster_type: Mapping[int, str],
        symmetries_by_cluster_type: Mapping[int, tuple[Matrix, ...]],
        port_semantics: Callable[[Any],
                                 tuple[tuple[str, ...], tuple[str, ...]]],
        outside_chemistry: Callable[[int], tuple[str, ...]],
        population_by_cluster_type: Mapping[
            int, tuple[tuple[str, int], ...]] | None = None,
) -> PortGraphProduction:
    """Adapt a ``MacroType`` without treating numeric type/pose keys as semantics.

    ``port_semantics`` must remove scale-dependent pose quantization while
    retaining connection kind and overlap chemistry.  This explicit callback
    prevents a raw atlas pose key from silently defining stationarity.
    """
    placements = tuple(sorted(macro.child_placements,
                              key=lambda item: item.node))
    if tuple(item.node for item in placements) != tuple(range(len(placements))):
        raise ValueError("macro child nodes must be contiguous")
    children = tuple(ProductionChild(
        chemistry_by_cluster_type[item.cluster_type],
        chirality_by_cluster_type[item.cluster_type], item.rotation,
        item.translation, symmetries_by_cluster_type[item.cluster_type],
        (() if population_by_cluster_type is None else
         population_by_cluster_type[item.cluster_type]))
        for item in placements)
    ports = []
    for edge in macro.edges:
        key, overlap = port_semantics(edge.port)
        ports.append(ProductionPort(
            edge.source, edge.target, key, overlap))
    boundaries = []
    for slot in macro.boundary_slots:
        key, overlap = port_semantics(slot.port)
        boundaries.append(ProductionBoundary(
            slot.node, slot.direction, outside_chemistry(slot.outside_type),
            key, overlap))
    return PortGraphProduction(
        children, tuple(ports), tuple(boundaries))
