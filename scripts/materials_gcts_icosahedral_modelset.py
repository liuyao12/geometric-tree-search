#!/usr/bin/env python3
"""Coupled icosahedral 6D model-set inference and growth.

The input is a three-species physical-space point cloud.  The learner infers
the quadratic unit, reconstructs integer 6D lifts, learns a spherical internal
acceptance window and radial chemical decoration, and grows a larger patch.
Hidden lifts and generator thresholds are used only for final evaluation.

The spherical window is an exact algorithmic icosahedral model-set control, not
the canonical triacontahedral-window Ammann tiling and not an experimental
material structure.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from materials_gcts_generic import AtomicConfiguration

Vector = Tuple[float, float, float]
Lift = Tuple[int, int, int, int, int, int]

HIDDEN_UNIT = (1.0 + math.sqrt(5.0)) / 2.0
HIDDEN_CONJUGATE = -1.0 / HIDDEN_UNIT
HIDDEN_WINDOW = 1.5
HIDDEN_SPECIES_THRESHOLDS = (0.75, 1.125)


@dataclass(frozen=True)
class IcosahedralGrowthResult:
    input_atoms: int
    chemical_species: int
    inferred_quadratic_unit: float
    quadratic_unit_error: float
    maximum_lift_residual: float
    inferred_window_radius: float
    inferred_species_thresholds: Tuple[float, float]
    grown_atoms: int
    atom_growth_factor: float
    new_atoms: int
    lift_set_precision: float
    lift_set_recall: float
    grown_species_accuracy: float
    maximum_position_error: float
    local_overlap_forced: int
    local_overlap_hidden: int
    local_overlap_accuracy: float
    hybrid_markov_accuracy: float


def star_vectors(unit: float) -> Tuple[Vector, ...]:
    return (
        (1.0, unit, 0.0), (-1.0, unit, 0.0),
        (0.0, 1.0, unit), (0.0, -1.0, unit),
        (unit, 0.0, 1.0), (unit, 0.0, -1.0),
    )


def project(lift: Lift, vectors: Sequence[Vector]) -> Vector:
    return tuple(sum(lift[index] * vectors[index][axis] for index in range(6))
                 for axis in range(3))  # type: ignore[return-value]


def vector_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def hidden_species(internal_radius: float) -> str:
    if internal_radius < HIDDEN_SPECIES_THRESHOLDS[0]:
        return "X"
    if internal_radius < HIDDEN_SPECIES_THRESHOLDS[1]:
        return "Y"
    return "Z"


def oracle_patch(
    lift_bound: int,
    physical_radius: float,
) -> Tuple[AtomicConfiguration, Dict[Lift, str]]:
    physical_vectors = star_vectors(HIDDEN_UNIT)
    internal_vectors = star_vectors(HIDDEN_CONJUGATE)
    positions = []
    species = []
    lifts: Dict[Lift, str] = {}
    for lift in itertools.product(range(-lift_bound, lift_bound + 1), repeat=6):
        physical = project(lift, physical_vectors)
        internal = project(lift, internal_vectors)
        internal_radius = vector_norm(internal)
        if (vector_norm(physical) <= physical_radius + 1e-10 and
                internal_radius <= HIDDEN_WINDOW + 1e-10):
            chemical = hidden_species(internal_radius)
            positions.append(physical)
            species.append(chemical)
            lifts[lift] = chemical
    configuration = AtomicConfiguration(
        "Icosahedral-6D-model-set", tuple(positions), tuple(species), None, False,
        "Exact six-dimensional icosahedral cut-and-project control with a "
        "spherical internal window and three radial chemical shells.")
    return configuration, lifts


def oracle_patch_fast(
    lift_bound: int,
    physical_radius: float,
) -> Tuple[AtomicConfiguration, Dict[Lift, str]]:
    """Exact meet-in-the-middle oracle for larger benchmark patches."""
    physical_vectors = star_vectors(HIDDEN_UNIT)
    internal_vectors = star_vectors(HIDDEN_CONJUGATE)
    coefficient_range = range(-lift_bound, lift_bound + 1)

    def partials(offset):
        result = []
        for coefficients in itertools.product(coefficient_range, repeat=3):
            physical = tuple(sum(
                coefficients[index] * physical_vectors[offset + index][axis]
                for index in range(3)) for axis in range(3))
            internal = tuple(sum(
                coefficients[index] * internal_vectors[offset + index][axis]
                for index in range(3)) for axis in range(3))
            result.append((coefficients, physical, internal))
        return tuple(result)

    left, right = partials(0), partials(3)
    cell = HIDDEN_WINDOW
    grid = {}
    for item in right:
        key = tuple(math.floor(value / cell) for value in item[2])
        grid.setdefault(key, []).append(item)
    positions = []
    species = []
    lifts = {}
    for left_coefficients, left_physical, left_internal in left:
        target = tuple(-value for value in left_internal)
        key = tuple(math.floor(value / cell) for value in target)
        for dx, dy, dz in itertools.product((-1, 0, 1), repeat=3):
            for right_coefficients, right_physical, right_internal in grid.get(
                    (key[0] + dx, key[1] + dy, key[2] + dz), ()):
                internal = tuple(left_internal[axis] + right_internal[axis]
                                 for axis in range(3))
                internal_radius = vector_norm(internal)
                if internal_radius > HIDDEN_WINDOW + 1e-10:
                    continue
                physical = tuple(left_physical[axis] + right_physical[axis]
                                 for axis in range(3))
                if vector_norm(physical) > physical_radius + 1e-10:
                    continue
                lift = left_coefficients + right_coefficients
                chemical = hidden_species(internal_radius)
                positions.append(physical)
                species.append(chemical)
                lifts[lift] = chemical
    configuration = AtomicConfiguration(
        "Icosahedral-6D-model-set", tuple(positions), tuple(species), None,
        False, "Exact meet-in-the-middle six-dimensional icosahedral "
        "cut-and-project control with a spherical internal window and three "
        "radial chemical shells.")
    return configuration, lifts


def algebraic_pair(
    value: float,
    unit: float,
    bound: int = 16,
    complexity_penalty: float = 1e-4,
) -> Tuple[int, int, float]:
    best = None
    for coefficient in range(-bound, bound + 1):
        integer = round(value - coefficient * unit)
        residual = abs(value - (integer + coefficient * unit))
        complexity = abs(integer) + abs(coefficient)
        candidate = (residual + complexity_penalty * complexity, complexity,
                     residual,
                     integer, coefficient)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    return best[3], best[4], best[2]


def infer_quadratic_unit(
    configuration: AtomicConfiguration,
    coefficient_bound: int = 16,
    complexity_penalty: float = 1e-4,
) -> Tuple[float, float]:
    candidates = [
        (integer + math.sqrt(integer * integer + 4.0)) / 2.0
        for integer in range(1, 5)
    ]
    scored = []
    values = [coordinate for point in configuration.positions
              for coordinate in point]
    for unit in candidates:
        residuals = [algebraic_pair(
            value, unit, coefficient_bound, complexity_penalty)[2]
            for value in values]
        scored.append((max(residuals), sum(residuals), unit))
    maximum, _, selected = min(scored)
    return selected, maximum


def lift_point(
    point: Vector,
    unit: float,
    coefficient_bound: int = 16,
    complexity_penalty: float = 1e-4,
) -> Tuple[Lift, float]:
    xa, xb, xr = algebraic_pair(
        point[0], unit, coefficient_bound, complexity_penalty)
    ya, yb, yr = algebraic_pair(
        point[1], unit, coefficient_bound, complexity_penalty)
    za, zb, zr = algebraic_pair(
        point[2], unit, coefficient_bound, complexity_penalty)
    values = (
        (yb + xa) / 2, (yb - xa) / 2,
        (zb + ya) / 2, (zb - ya) / 2,
        (xb + za) / 2, (xb - za) / 2,
    )
    lift = tuple(round(value) for value in values)
    integrality = max(abs(value - round(value)) for value in values)
    reconstructed = project(lift, star_vectors(unit))  # type: ignore[arg-type]
    residual = max(xr, yr, zr, integrality,
                   vector_norm(tuple(a - b for a, b in zip(point,
                                                            reconstructed))))
    return lift, residual  # type: ignore[return-value]


def simplest_rational_between(
    lower: float,
    upper: float,
    maximum_denominator: int = 32,
) -> float:
    if not lower < upper:
        raise ValueError("empty rational interval")
    midpoint = (lower + upper) / 2
    for denominator in range(1, maximum_denominator + 1):
        first = math.floor(lower * denominator) + 1
        last = math.ceil(upper * denominator) - 1
        if first <= last:
            numerator = min(range(first, last + 1),
                            key=lambda value: abs(value / denominator - midpoint))
            return float(Fraction(numerator, denominator))
    return midpoint


def infer_model(
    configuration: AtomicConfiguration,
    coefficient_bound: int = 16,
    complexity_penalty: float = 1e-4,
) -> Tuple[float, Dict[Lift, str], float, Tuple[float, float], float]:
    unit, field_residual = infer_quadratic_unit(
        configuration, coefficient_bound, complexity_penalty)
    conjugate = -1.0 / unit
    lifted: Dict[Lift, str] = {}
    maximum_lift_residual = 0.0
    for point, chemical in zip(configuration.positions, configuration.species):
        lift, residual = lift_point(
            point, unit, coefficient_bound, complexity_penalty)
        maximum_lift_residual = max(maximum_lift_residual, residual)
        lifted[lift] = chemical
    bound = max(abs(value) for lift in lifted for value in lift)
    physical_radius = math.ceil(max(vector_norm(point)
                                    for point in configuration.positions) - 1e-9)
    physical_vectors = star_vectors(unit)
    internal_vectors = star_vectors(conjugate)
    accepted_radii = []
    rejected_radii = []
    for lift in itertools.product(range(-bound, bound + 1), repeat=6):
        if vector_norm(project(lift, physical_vectors)) > physical_radius + 1e-8:
            continue
        radius = vector_norm(project(lift, internal_vectors))
        (accepted_radii if lift in lifted else rejected_radii).append(radius)
    maximum_accepted = max(accepted_radii)
    minimum_rejected = min(radius for radius in rejected_radii
                           if radius > maximum_accepted)
    window = simplest_rational_between(maximum_accepted, minimum_rejected)

    radii_by_species: Dict[str, List[float]] = {}
    for lift, chemical in lifted.items():
        radii_by_species.setdefault(chemical, []).append(
            vector_norm(project(lift, internal_vectors)))
    ordered_species = sorted(radii_by_species,
                             key=lambda chemical: sum(radii_by_species[chemical]) /
                             len(radii_by_species[chemical]))
    thresholds = []
    for left, right in zip(ordered_species, ordered_species[1:]):
        # Chemical shells transform with the acceptance window.  Encoding a
        # rational fraction of the learned window is both scale covariant and
        # shorter than two unrelated absolute radii.
        normalized = simplest_rational_between(
            max(radii_by_species[left]) / window,
            min(radii_by_species[right]) / window)
        thresholds.append(normalized * window)
    return unit, lifted, window, tuple(thresholds), max(
        field_residual, maximum_lift_residual)


def learned_species(
    radius: float,
    ordered_species: Sequence[str],
    thresholds: Sequence[float],
) -> str:
    for index, threshold in enumerate(thresholds):
        if radius < threshold:
            return ordered_species[index]
    return ordered_species[-1]


def evaluate() -> IcosahedralGrowthResult:
    configuration, hidden_input_lifts = oracle_patch(3, 9.0)
    unit, lifted, window, thresholds, lift_residual = infer_model(configuration)
    conjugate = -1.0 / unit
    physical_vectors = star_vectors(unit)
    internal_vectors = star_vectors(conjugate)
    species_radii: Dict[str, List[float]] = {}
    for lift, chemical in lifted.items():
        species_radii.setdefault(chemical, []).append(
            vector_norm(project(lift, internal_vectors)))
    ordered_species = sorted(species_radii,
                             key=lambda chemical: sum(species_radii[chemical]) /
                             len(species_radii[chemical]))

    predicted: Dict[Lift, str] = {}
    predicted_positions: Dict[Lift, Vector] = {}
    for lift in itertools.product(range(-4, 5), repeat=6):
        physical = project(lift, physical_vectors)
        internal_radius = vector_norm(project(lift, internal_vectors))
        if vector_norm(physical) <= 15.0 + 1e-10 and internal_radius <= window:
            predicted[lift] = learned_species(
                internal_radius, ordered_species, thresholds)
            predicted_positions[lift] = physical
    _, oracle = oracle_patch(4, 15.0)
    predicted_set, oracle_set = set(predicted), set(oracle)
    intersection = predicted_set & oracle_set
    species_accuracy = sum(predicted[lift] == oracle[lift]
                           for lift in intersection) / len(intersection)
    oracle_vectors = star_vectors(HIDDEN_UNIT)
    position_error = max(
        vector_norm(tuple(a - b for a, b in zip(predicted_positions[lift],
                                                project(lift, oracle_vectors))))
        for lift in intersection)

    from materials_gcts_generic_overlap import evaluate as evaluate_overlap
    local_results = [evaluate_overlap(configuration, seed=seed)
                     for seed in range(5)]
    local_hidden = sum(result.hidden_atoms for result in local_results)
    local_forced = sum(result.overlap_forced for result in local_results)
    local_correct = sum(result.overlap_forced * result.overlap_accuracy
                        for result in local_results)
    hybrid_correct = sum(result.hidden_atoms * result.hybrid_markov_accuracy
                         for result in local_results)
    return IcosahedralGrowthResult(
        len(configuration.positions),
        len(set(configuration.species)),
        unit,
        abs(unit - HIDDEN_UNIT),
        lift_residual,
        window,
        thresholds,  # type: ignore[arg-type]
        len(predicted),
        len(predicted) / len(configuration.positions),
        len(predicted_set - set(hidden_input_lifts)),
        len(intersection) / len(predicted_set),
        len(intersection) / len(oracle_set),
        species_accuracy,
        position_error,
        local_forced,
        local_hidden,
        local_correct / local_forced,
        hybrid_correct / local_hidden,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if arguments.json else result)


if __name__ == "__main__":
    main()
