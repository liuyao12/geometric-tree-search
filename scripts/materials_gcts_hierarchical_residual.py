#!/usr/bin/env python3
"""Learn a recursive displacement marking on top of a colored crystal quotient.

The input is only a finite colored point cloud.  A short same-species frame
recovers the reference quotient.  Residual offsets are then represented as a
sum of octant sections, one on each binary parent level.  If those sections
form a low-residual geometric recurrence, the next parent marking can be
extrapolated without copying the entire observed atom block.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Dict, List, Sequence, Tuple

import materials_gcts_blind_continuation as blind
from materials_gcts_generic import (
    AtomicConfiguration, fractional_to_cartesian, inverse3, matvec)

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class HierarchicalResidualRule:
    basis: Matrix
    cell_minimum: Tuple[int, int, int]
    input_side: int
    motif: Tuple[Tuple[str, float, float, float], ...]
    level_markings: Tuple[Tuple[Vector, ...], ...]
    marking_ratio: float
    fit_rms: float
    recurrence_rms: float
    fit_relative_error: float
    recurrence_relative_error: float
    deterministic: bool


@dataclass(frozen=True)
class HierarchicalResidualBenchmark:
    input_atoms: int
    learned_motif_atoms: int
    learned_parent_levels: int
    learned_marking_ratio: float
    marking_fit_rms: float
    marking_recurrence_rms: float
    marking_fit_relative_error: float
    marking_recurrence_relative_error: float
    action_counts: Tuple[int, ...]
    atom_counts: Tuple[int, ...]
    exact_recursive_growth: bool
    flat_copy_coordinate_rms: float
    marked_coordinate_rms: float
    marked_improvement: float
    atomwise_actions_per_macro_action: float
    rigid_motion_invariant: bool
    random_residual_rejected: bool


@dataclass(frozen=True)
class DefectAwareResidualRule:
    structural_rule: HierarchicalResidualRule
    missing_sites: Tuple[Tuple[Tuple[int, int, int], str], ...]
    added_atoms: Tuple[Tuple[str, Vector], ...]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _learn_short_translation_frame(configuration: AtomicConfiguration) -> Matrix:
    by_species: Dict[str, List[Vector]] = {}
    for point, chemical in zip(configuration.positions, configuration.species):
        by_species.setdefault(chemical, []).append(point)
    vectors = []
    shortest = math.inf
    for points in by_species.values():
        for index, left in enumerate(points):
            for right in points[index + 1:]:
                vector = tuple(right[axis] - left[axis] for axis in range(3))
                length = _norm(vector)
                if length < shortest:
                    shortest = length
                vectors.append((length, vector))
    local = [(length, vector) for length, vector in vectors
             if length <= shortest * 1.16]
    clusters: List[Dict[str, object]] = []
    for length, vector in local:
        unit = tuple(value / length for value in vector)
        for cluster in clusters:
            representative = cluster["unit"]
            cosine = _dot(unit, representative)  # type: ignore[arg-type]
            if abs(cosine) < math.cos(0.10):
                continue
            aligned = vector if cosine >= 0 else tuple(-value for value in vector)
            cluster["vectors"].append(aligned)  # type: ignore[union-attr]
            values = cluster["vectors"]  # type: ignore[assignment]
            mean = tuple(sum(item[axis] for item in values) / len(values)
                         for axis in range(3))
            cluster["unit"] = tuple(value / _norm(mean) for value in mean)
            break
        else:
            clusters.append({"unit": unit, "vectors": [vector]})
    ranked = sorted(clusters,
                    key=lambda item: -len(item["vectors"]))  # type: ignore[arg-type]
    candidates = []
    for combo in itertools.combinations(ranked[:8], 3):
        means = []
        for cluster in combo:
            values = cluster["vectors"]
            means.append(tuple(sum(item[axis] for item in values) / len(values)
                               for axis in range(3)))
        volume = abs(_dot(means[0], _cross(means[1], means[2])))
        normalized = volume / math.prod(_norm(item) for item in means)
        if normalized > 0.65:
            candidates.append((sum(len(item["vectors"]) for item in combo),
                               normalized, tuple(means)))
    if not candidates:
        raise ValueError("no three-dimensional short translation frame")
    return max(candidates, key=lambda item: item[:2])[2]  # type: ignore[return-value]


def _circular_mean(values: Sequence[float]) -> float:
    angle = math.atan2(sum(math.sin(2 * math.pi * value) for value in values),
                       sum(math.cos(2 * math.pi * value) for value in values))
    result = (angle / (2 * math.pi)) % 1.0
    return result - 1.0 if result > 0.75 else result


def _solve_least_squares(rows, values):
    width = len(rows[0])
    normal = [[0.0] * width for _ in range(width)]
    right = [0.0] * width
    for row, value in zip(rows, values):
        for i, left in enumerate(row):
            right[i] += left * value
            for j in range(i, width):
                normal[i][j] += left * row[j]
    for i in range(width):
        for j in range(i):
            normal[i][j] = normal[j][i]
        normal[i][i] += 1e-12
    for pivot in range(width):
        row = max(range(pivot, width), key=lambda index: abs(normal[index][pivot]))
        normal[pivot], normal[row] = normal[row], normal[pivot]
        right[pivot], right[row] = right[row], right[pivot]
        scale = normal[pivot][pivot]
        if abs(scale) < 1e-14:
            raise ValueError("singular residual marking fit")
        for column in range(pivot, width):
            normal[pivot][column] /= scale
        right[pivot] /= scale
        for other in range(width):
            if other == pivot:
                continue
            factor = normal[other][pivot]
            if abs(factor) < 1e-18:
                continue
            for column in range(pivot, width):
                normal[other][column] -= factor * normal[pivot][column]
            right[other] -= factor * right[pivot]
    return tuple(right)


def _section_features(code: int) -> Tuple[float, float, float, float]:
    """Octant interactions with the 000 child fixed as the zero section.

    Constant and one-bit modes belong to the motif and translation frame.
    Removing them makes the frame identifiable even when an edge sample is
    missing; the remaining pair/triple interactions are genuine parent
    markings rather than a disguised lattice strain.
    """
    sx = 1.0 if code & 4 else -1.0
    sy = 1.0 if code & 2 else -1.0
    sz = 1.0 if code & 1 else -1.0
    return (sx * sy - 1.0, sx * sz - 1.0, sy * sz - 1.0,
            sx * sy * sz + 1.0)


def learn_residual_rule(configuration: AtomicConfiguration) -> HierarchicalResidualRule:
    basis = _learn_short_translation_frame(configuration)
    fractional = tuple(matvec(inverse3(basis), point)
                       for point in configuration.positions)
    chemicals = tuple(sorted(set(configuration.species)))
    motif_guess = {
        chemical: tuple(_circular_mean([
            point[axis] % 1.0 for point, item in zip(fractional,
                                                     configuration.species)
            if item == chemical]) for axis in range(3))
        for chemical in chemicals}
    # Circular residues are defined only modulo an integer.  Choose those
    # integer representatives so every chemical motif shares the same finite
    # cell box; otherwise a generic rigid translation can make one species
    # appear to occupy an extra boundary cell.
    preliminary_minimum = {}
    for chemical in chemicals:
        cells = [tuple(round(point[axis] - motif_guess[chemical][axis])
                       for axis in range(3))
                 for point, item in zip(fractional, configuration.species)
                 if item == chemical]
        preliminary_minimum[chemical] = tuple(
            min(cell[axis] for cell in cells) for axis in range(3))
    target_minimum = preliminary_minimum[chemicals[0]]
    motif_guess = {
        chemical: tuple(motif_guess[chemical][axis] +
                        preliminary_minimum[chemical][axis] -
                        target_minimum[axis] for axis in range(3))
        for chemical in chemicals}
    assignments = []
    for point, chemical in zip(fractional, configuration.species):
        residue = motif_guess[chemical]
        cell = tuple(round(point[axis] - residue[axis]) for axis in range(3))
        assignments.append((chemicals.index(chemical), cell, point))
    minimum = tuple(min(item[1][axis] for item in assignments)
                    for axis in range(3))
    maximum = tuple(max(item[1][axis] for item in assignments)
                    for axis in range(3))
    counts = tuple(maximum[axis] - minimum[axis] + 1 for axis in range(3))
    if len(set(counts)) != 1 or counts[0] & (counts[0] - 1):
        raise ValueError("residual parent must be a dyadic finite box")
    levels = round(math.log2(counts[0]))
    motif_count = len(chemicals)
    section_width = 4
    width = motif_count + levels * section_width
    rows = []
    for motif_id, cell, _ in assignments:
        row = [0.0] * width
        row[motif_id] = 1.0
        local = tuple(cell[axis] - minimum[axis] for axis in range(3))
        for level in range(levels):
            code = (((local[0] >> level) & 1) << 2 |
                    ((local[1] >> level) & 1) << 1 |
                    ((local[2] >> level) & 1))
            for feature, value in enumerate(_section_features(code)):
                row[motif_count + level * section_width + feature] = value
        rows.append(row)
    # Jointly refine the approximate short-vector frame with the motif and all
    # observed parent markings.  Averaging local edge vectors is exact for a
    # complete balanced box but a single frontier vacancy removes edges
    # asymmetrically.  The joint model keeps that missing sample local instead
    # of leaking its bias into every generated coordinate.
    joint_rows = [list(cell) + row
                  for (_, cell, _), row in zip(assignments, rows)]
    joint = tuple(_solve_least_squares(
        joint_rows, [point[axis] for point in configuration.positions])
        for axis in range(3))
    refined_basis = tuple(tuple(joint[cartesian][fractional_axis]
                                for cartesian in range(3))
                          for fractional_axis in range(3))
    refined_inverse = inverse3(refined_basis)  # type: ignore[arg-type]
    coefficient_vectors = [tuple(joint[axis][3 + index]
                                 for axis in range(3))
                           for index in range(width)]
    fractional_vectors = [matvec(refined_inverse, vector)
                          for vector in coefficient_vectors]
    coefficients = tuple(tuple(vector[axis]
                               for vector in fractional_vectors)
                         for axis in range(3))
    refined_fractional = tuple(matvec(refined_inverse, point)
                               for point in configuration.positions)
    assignments = [(motif_id, cell, point)
                   for (motif_id, cell, _), point in zip(assignments,
                                                         refined_fractional)]
    motif = tuple((chemical,) + tuple(coefficients[axis][index]
                                       for axis in range(3))
                  for index, chemical in enumerate(chemicals))
    level_markings = []
    for level in range(levels):
        values = []
        for code in range(8):
            features = _section_features(code)
            values.append(tuple(sum(
                features[feature] * coefficients[axis][
                    motif_count + level * section_width + feature]
                for feature in range(section_width)) for axis in range(3)))
        level_markings.append(tuple(values))
    numerator = denominator = 0.0
    for left, right in zip(level_markings, level_markings[1:]):
        for first, second in zip(left, right):
            numerator += _dot(first, second)
            denominator += _dot(first, first)
    ratio = numerator / denominator
    recurrence_errors = [
        second[axis] - ratio * first[axis]
        for left, right in zip(level_markings, level_markings[1:])
        for first, second in zip(left, right) for axis in range(3)]
    recurrence_rms = math.sqrt(sum(value * value for value in recurrence_errors) /
                               len(recurrence_errors))
    predictions = []
    for row in rows:
        predictions.append(tuple(sum(row[index] * coefficients[axis][index]
                                     for index in range(width))
                                 for axis in range(3)))
    errors = [predictions[index][axis] -
              (assignments[index][2][axis] - assignments[index][1][axis])
              for index in range(len(assignments)) for axis in range(3)]
    fit_rms = math.sqrt(sum(value * value for value in errors) / len(errors))
    response_means = {}
    for motif_id in range(motif_count):
        for axis in range(3):
            values = [point[axis] - cell[axis]
                      for item_id, cell, point in assignments
                      if item_id == motif_id]
            response_means[(motif_id, axis)] = sum(values) / len(values)
    variation = [
        (point[axis] - cell[axis]) - response_means[(motif_id, axis)]
        for motif_id, cell, point in assignments for axis in range(3)]
    variation_rms = math.sqrt(sum(value * value for value in variation) /
                              len(variation))
    fit_relative = fit_rms / max(variation_rms, 1e-12)
    marking_values = [value for level in level_markings[1:]
                      for item in level for value in item]
    marking_rms = math.sqrt(sum(value * value for value in marking_values) /
                            max(1, len(marking_values)))
    recurrence_relative = recurrence_rms / max(marking_rms, 1e-12)
    deterministic = fit_relative < 0.10 and recurrence_relative < 0.10
    return HierarchicalResidualRule(
        refined_basis, minimum, counts[0], motif, tuple(level_markings), ratio,
        fit_rms, recurrence_rms, fit_relative, recurrence_relative,
        deterministic)


def apply_residual_rule(
    rule: HierarchicalResidualRule, actions: int,
    *, include_new_parent_markings: bool = True,
) -> AtomicConfiguration:
    if actions < 0:
        raise ValueError("actions must be nonnegative")
    if not rule.deterministic:
        raise ValueError("residual marking failed its recurrence gate")
    levels = list(rule.level_markings)
    for _ in range(actions):
        previous = levels[-1]
        levels.append(tuple(tuple(rule.marking_ratio * value for value in item)
                            for item in previous))
    side = rule.input_side * 2 ** actions
    positions = []
    species = []
    for local in itertools.product(range(side), repeat=3):
        cell = tuple(rule.cell_minimum[axis] + local[axis]
                     for axis in range(3))
        displacement = [0.0, 0.0, 0.0]
        active_levels = len(rule.level_markings) if not include_new_parent_markings else len(levels)
        for level in range(active_levels):
            code = (((local[0] >> level) & 1) << 2 |
                    ((local[1] >> level) & 1) << 1 |
                    ((local[2] >> level) & 1))
            for axis in range(3):
                displacement[axis] += levels[level][code][axis]
        for chemical, fx, fy, fz in rule.motif:
            fractional = tuple(cell[axis] + (fx, fy, fz)[axis] +
                               displacement[axis] for axis in range(3))
            positions.append(fractional_to_cartesian(rule.basis, fractional))
            species.append(chemical)
    return AtomicConfiguration(
        "hierarchical-residual-grown", tuple(positions), tuple(species),
        None, False, "Recursive octant-section displacement marking")


def learn_defect_aware_rule(
    configuration: AtomicConfiguration,
) -> DefectAwareResidualRule:
    """Separate a recurrent parent field from sparse, nonrecurring residuals."""
    counts = Counter(configuration.species)
    maximum = max(counts.values())
    structural_species = {chemical for chemical, count in counts.items()
                          if count >= 0.25 * maximum}
    positions = tuple(point for point, chemical in zip(
        configuration.positions, configuration.species)
                      if chemical in structural_species)
    species = tuple(chemical for chemical in configuration.species
                    if chemical in structural_species)
    structural = AtomicConfiguration(
        configuration.name + "-structural", positions, species, None, False,
        configuration.provenance)
    rule = learn_residual_rule(structural)
    reconstructed = apply_residual_rule(rule, 0)
    expected = {(blind._site_key(point), chemical): point
                for point, chemical in zip(reconstructed.positions,
                                           reconstructed.species)}
    observed = {(blind._site_key(point), chemical): point
                for point, chemical in zip(configuration.positions,
                                           configuration.species)}
    missing = tuple(sorted(expected.keys() - observed.keys()))
    added = tuple(sorted((site[1], observed[site])
                         for site in observed.keys() - expected.keys()))
    sparse_limit = max(4, round(0.02 * len(configuration.positions)))
    if len(missing) + len(added) > sparse_limit:
        raise ValueError("residual is not sparse enough to remain local")
    return DefectAwareResidualRule(rule, missing, added)


def apply_defect_aware_rule(
    rule: DefectAwareResidualRule, actions: int,
) -> AtomicConfiguration:
    grown = apply_residual_rule(rule.structural_rule, actions)
    atoms = {(blind._site_key(point), chemical): point
             for point, chemical in zip(grown.positions, grown.species)}
    for site in rule.missing_sites:
        atoms.pop(site, None)
    for chemical, point in rule.added_atoms:
        atoms[(blind._site_key(point), chemical)] = point
    ordered = sorted(atoms.items())
    return AtomicConfiguration(
        grown.name + "-defect-aware",
        tuple(point for _, point in ordered),
        tuple(site[1] for site, _ in ordered), None, False,
        "Recursive parent marking with sparse residual carried once")


_BASE_MARKING = (
    (0.0, 0.0, 0.0),
    (0.020, -0.008, 0.006),
    (-0.010, 0.018, 0.004),
    (0.012, 0.009, -0.017),
    (0.012, 0.009, -0.017),
    (-0.010, 0.018, 0.004),
    (0.020, -0.008, 0.006),
    (0.0, 0.0, 0.0),
)
_HIDDEN_RATIO = 0.58


def _hidden_configuration(side: int, transform=None) -> AtomicConfiguration:
    lattice = 2.887
    levels = round(math.log2(side))
    positions = []
    species = []
    for cell in itertools.product(range(side), repeat=3):
        displacement = [0.0, 0.0, 0.0]
        for level in range(levels):
            code = (((cell[0] >> level) & 1) << 2 |
                    ((cell[1] >> level) & 1) << 1 |
                    ((cell[2] >> level) & 1))
            for axis in range(3):
                displacement[axis] += (_HIDDEN_RATIO ** level *
                                       _BASE_MARKING[code][axis])
        for residue, chemical in (((0.0, 0.0, 0.0), "Ni"),
                                  ((0.5, 0.5, 0.5), "Al")):
            point = tuple(lattice * (cell[axis] + residue[axis] +
                                     displacement[axis]) for axis in range(3))
            positions.append(transform(point) if transform else point)
            species.append(chemical)
    return AtomicConfiguration(
        "hidden-hierarchical-B2", tuple(positions), tuple(species), None,
        False, "Held-out recursive displacement control")


def _random_residual_configuration(side: int, seed: int = 91):
    generator = random.Random(seed)
    lattice = 2.887
    positions = []
    species = []
    for cell in itertools.product(range(side), repeat=3):
        displacement = tuple(generator.uniform(-0.025, 0.025)
                             for _ in range(3))
        for residue, chemical in (((0.0, 0.0, 0.0), "Ni"),
                                  ((0.5, 0.5, 0.5), "Al")):
            positions.append(tuple(lattice * (cell[axis] + residue[axis] +
                                               displacement[axis])
                                   for axis in range(3)))
            species.append(chemical)
    return AtomicConfiguration(
        "random-residual-B2", tuple(positions), tuple(species), None, False,
        "IID displacement null control")


def _sites(configuration):
    return {(blind._site_key(point), chemical)
            for point, chemical in zip(configuration.positions,
                                       configuration.species)}


def _coordinate_rms(predicted, expected):
    cell_size = 0.5
    buckets = {}
    for point, chemical in zip(expected.positions, expected.species):
        key = (chemical,) + tuple(math.floor(value / cell_size)
                                  for value in point)
        buckets.setdefault(key, []).append(point)
    squared = []
    for point, chemical in zip(predicted.positions, predicted.species):
        center = tuple(math.floor(value / cell_size) for value in point)
        candidates = []
        for offset in itertools.product((-1, 0, 1), repeat=3):
            key = (chemical,) + tuple(center[axis] + offset[axis]
                                      for axis in range(3))
            candidates.extend(buckets.get(key, ()))
        if not candidates:
            raise ValueError("no nearby same-species oracle site")
        squared.append(min(sum((point[axis] - target[axis]) ** 2
                               for axis in range(3))
                           for target in candidates))
    return math.sqrt(sum(squared) / (3 * len(squared)))


def evaluate() -> HierarchicalResidualBenchmark:
    training = _hidden_configuration(8)
    rule = learn_residual_rule(training)
    grown = tuple(apply_residual_rule(rule, action) for action in (0, 1, 2))
    expected = tuple(_hidden_configuration(side) for side in (8, 16, 32))
    exact = all(_sites(left) == _sites(right)
                for left, right in zip(grown, expected))
    flat = apply_residual_rule(rule, 1, include_new_parent_markings=False)
    flat_rms = _coordinate_rms(flat, expected[1])
    marked_rms = _coordinate_rms(grown[1], expected[1])

    angle = 0.41
    cosine, sine = math.cos(angle), math.sin(angle)
    def move(point):
        x, y, z = point
        return (cosine * x - sine * z + 3.2,
                y - 1.7, sine * x + cosine * z + 0.8)
    moved_training = _hidden_configuration(8, move)
    moved_rule = learn_residual_rule(moved_training)
    moved = apply_residual_rule(moved_rule, 1)
    moved_expected = _hidden_configuration(16, move)
    invariant = _sites(moved) == _sites(moved_expected)
    try:
        null_rule = learn_residual_rule(_random_residual_configuration(8))
        random_rejected = not null_rule.deterministic
    except ValueError:
        random_rejected = True
    counts = tuple(len(item.positions) for item in grown)
    generated = counts[-1] - counts[0]
    return HierarchicalResidualBenchmark(
        counts[0], len(rule.motif), len(rule.level_markings),
        rule.marking_ratio, rule.fit_rms, rule.recurrence_rms,
        rule.fit_relative_error, rule.recurrence_relative_error,
        (0, 1, 2), counts, exact, flat_rms, marked_rms,
        flat_rms / max(marked_rms, 1e-15), generated / 2.0, invariant,
        random_rejected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
