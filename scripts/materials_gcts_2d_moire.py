#!/usr/bin/env python3
"""Finite colored hexagonal bilayers for the generic GCTS benchmark.

The learner is given only atomic positions and species.  Hexagonal lattice
coordinates and twist labels are used by the fixture generator and scorer,
never by ``learn_bilayer_atlas``.  The learned atlas consists of a colored
two-atom cluster, its two translation ports, and one pose per disconnected
sheet.  This is the smallest useful 2D cluster-of-clusters baseline: the same
cluster is reused in two freely rotated poses, while their relative pose is a
finite marking.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from materials_gcts_generic import AtomicConfiguration

Vector = Tuple[float, float, float]
Vector2 = Tuple[float, float]


@dataclass(frozen=True)
class SheetAtlas:
    anchor: Vector
    translations: Tuple[Vector, Vector]
    basis_offset: Vector
    anchor_species: str
    basis_species: str
    atoms_covered: int
    orientation_degrees: float


@dataclass(frozen=True)
class BilayerAtlas:
    sheets: Tuple[SheetAtlas, ...]
    cluster_isometry_classes: int
    cluster_pose_states: int
    relative_pose_marking_degrees: float
    seed_atoms_covered: int
    seed_atoms: int
    common_translation_rank: int
    shortest_common_translation: Optional[float]


@dataclass(frozen=True)
class MoireBenchmarkCase:
    system: str
    seed_atoms: int
    heldout_atoms: int
    chemical_species: int
    inferred_intrinsic_dimension: float
    learned_sheets: int
    learned_cluster_isometry_classes: int
    learned_cluster_pose_states: int
    relative_pose_marking_degrees: float
    common_translation_rank: int
    shortest_common_translation: Optional[float]
    classification: str
    seed_cover_fraction: float
    heldout_position_precision: float
    heldout_position_recall: float
    heldout_chemical_accuracy: float
    areal_growth_per_radius_doubling: float
    projected_actions_to_million: int
    heldout_positions_used_for_learning: bool
    crystallographic_label_used_for_learning: bool
    physical_potential_used: bool


def _rotate(point: Vector2, angle: float) -> Vector2:
    cosine, sine = math.cos(angle), math.sin(angle)
    return (cosine * point[0] - sine * point[1],
            sine * point[0] + cosine * point[1])


def commensurate_twist(m: int, n: int) -> float:
    """Return the standard commensurate twist of two triangular lattices."""
    if m <= n or n < 0:
        raise ValueError("commensurate indices require m > n >= 0")
    numerator = m * m + 4 * m * n + n * n
    denominator = 2 * (m * m + m * n + n * n)
    return math.acos(max(-1.0, min(1.0, numerator / denominator)))


def hexagonal_bilayer(
    name: str,
    radius: float,
    twist: float,
    lattice_constant: float = 2.50,
    layer_separation: float = 3.33,
    registry_shift: Vector2 = (0.0, 0.0),
    species: Tuple[str, str] = ("B", "N"),
) -> AtomicConfiguration:
    """Generate an independently clipped, finite hBN-like bilayer disk."""
    a1 = (lattice_constant, 0.0)
    a2 = (0.5 * lattice_constant, 0.5 * math.sqrt(3.0) * lattice_constant)
    basis = ((0.0, 0.0),
             ((a1[0] + a2[0]) / 3.0, (a1[1] + a2[1]) / 3.0))
    extent = int(math.ceil(radius / lattice_constant)) + 4
    positions: List[Vector] = []
    colors: List[str] = []
    for layer, (angle, shift, z) in enumerate((
        (0.0, (0.0, 0.0), -0.5 * layer_separation),
        (twist, registry_shift, 0.5 * layer_separation),
    )):
        del layer
        for i in range(-extent, extent + 1):
            for j in range(-extent, extent + 1):
                origin = (i * a1[0] + j * a2[0],
                          i * a1[1] + j * a2[1])
                for offset, chemical in zip(basis, species):
                    xy = _rotate((origin[0] + offset[0],
                                  origin[1] + offset[1]), angle)
                    xy = (xy[0] + shift[0], xy[1] + shift[1])
                    if xy[0] * xy[0] + xy[1] * xy[1] <= radius * radius + 1e-9:
                        positions.append((xy[0], xy[1], z))
                        colors.append(chemical)
    order = sorted(range(len(positions)), key=lambda k: (
        round(positions[k][2], 8), round(positions[k][0], 8),
        round(positions[k][1], 8), colors[k]))
    return AtomicConfiguration(
        name, tuple(positions[k] for k in order),
        tuple(colors[k] for k in order), provenance=(
            "synthetic finite colored hexagonal bilayer; physical lengths are "
            "hBN-like but no energy model is used"))


def _distance(left: Vector, right: Vector) -> float:
    return math.sqrt(sum((left[k] - right[k]) ** 2 for k in range(3)))


def _components(configuration: AtomicConfiguration) -> Tuple[Tuple[int, ...], ...]:
    nearest = min(
        _distance(left, right)
        for i, left in enumerate(configuration.positions)
        for right in configuration.positions[i + 1:]
        if _distance(left, right) > 1e-8)
    cutoff = 1.08 * nearest
    unseen = set(range(len(configuration.positions)))
    components = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        stack = [root]
        component = [root]
        while stack:
            current = stack.pop()
            neighbors = [other for other in unseen
                         if _distance(configuration.positions[current],
                                      configuration.positions[other]) <= cutoff]
            for other in neighbors:
                unseen.remove(other)
                stack.append(other)
                component.append(other)
        components.append(tuple(sorted(component)))
    return tuple(sorted(components, key=lambda item: (-len(item), item[0])))


def _orientation(vector: Vector) -> float:
    return math.atan2(vector[1], vector[0]) % (math.pi / 3.0)


def _learn_sheet(configuration: AtomicConfiguration,
                 indices: Sequence[int]) -> SheetAtlas:
    colors = sorted(set(configuration.species[index] for index in indices))
    if len(colors) != 2:
        raise ValueError("the initial 2D atlas expects a binary colored sheet")
    populations = {color: [index for index in indices
                           if configuration.species[index] == color]
                   for color in colors}
    anchor_species = max(colors, key=lambda color: len(populations[color]))
    basis_species = colors[1 - colors.index(anchor_species)]
    anchor_index = min(populations[anchor_species], key=lambda index: sum(
        value * value for value in configuration.positions[index]))
    anchor = configuration.positions[anchor_index]
    same_vectors = []
    for index in populations[anchor_species]:
        if index == anchor_index:
            continue
        point = configuration.positions[index]
        vector = tuple(point[k] - anchor[k] for k in range(3))
        length = math.hypot(vector[0], vector[1])
        if length > 1e-8:
            same_vectors.append((length, vector))
    shortest = min(length for length, _ in same_vectors)
    shell = [vector for length, vector in same_vectors
             if abs(length - shortest) <= shortest * 1e-6]
    shell.sort(key=lambda vector: math.atan2(vector[1], vector[0]))
    vector1 = shell[0]
    vector2 = min(
        (vector for vector in shell
         if abs(vector1[0] * vector[1] - vector1[1] * vector[0]) > .4 * shortest ** 2),
        key=lambda vector: abs(
            (vector1[0] * vector[0] + vector1[1] * vector[1]) / shortest ** 2 - .5))
    basis_index = min(populations[basis_species], key=lambda index:
                      _distance(anchor, configuration.positions[index]))
    basis_offset = tuple(configuration.positions[basis_index][k] - anchor[k]
                         for k in range(3))
    return SheetAtlas(anchor, (vector1, vector2), basis_offset,
                      anchor_species, basis_species, len(indices),
                      math.degrees(_orientation(vector1)))


def _difference_keys(points: Sequence[Vector], tolerance: float = 1e-5
                     ) -> Dict[Tuple[int, int], float]:
    result: Dict[Tuple[int, int], float] = {}
    for i, left in enumerate(points):
        for right in points[i + 1:]:
            dx, dy = right[0] - left[0], right[1] - left[1]
            for x, y in ((dx, dy), (-dx, -dy)):
                key = (int(round(x / tolerance)), int(round(y / tolerance)))
                result[key] = math.hypot(x, y)
    return result


def _common_translation_basis(configuration: AtomicConfiguration,
                              sheets: Sequence[SheetAtlas],
                              tolerance: float = 1e-5) -> Tuple[int, Optional[float]]:
    difference_sets = []
    for sheet in sheets:
        points = [point for point, chemical in zip(
            configuration.positions, configuration.species)
                  if chemical == sheet.anchor_species and
                  abs(point[2] - sheet.anchor[2]) < tolerance]
        difference_sets.append(_difference_keys(points, tolerance))
    common = set(difference_sets[0]).intersection(*(set(item) for item in difference_sets[1:]))
    candidates = sorted((difference_sets[0][key], key) for key in common)
    if not candidates:
        return 0, None
    first_length, first = candidates[0]
    for _, second in candidates[1:]:
        cross = abs(first[0] * second[1] - first[1] * second[0])
        if cross > .05 * math.hypot(*first) * math.hypot(*second):
            return 2, first_length
    return 1, first_length


def learn_bilayer_atlas(configuration: AtomicConfiguration) -> BilayerAtlas:
    components = _components(configuration)
    meaningful = tuple(component for component in components if len(component) >= 8)
    sheets = tuple(_learn_sheet(configuration, component) for component in meaningful)
    if len(sheets) != 2 or sum(sheet.atoms_covered for sheet in sheets) != len(configuration.positions):
        raise ValueError("expected two fully covered connected atomic sheets")
    orientation_delta = abs(sheets[0].orientation_degrees - sheets[1].orientation_degrees) % 60.0
    orientation_delta = min(orientation_delta, 60.0 - orientation_delta)
    rank, shortest = _common_translation_basis(configuration, sheets)
    return BilayerAtlas(
        sheets=sheets, cluster_isometry_classes=1, cluster_pose_states=2,
        relative_pose_marking_degrees=orientation_delta,
        seed_atoms_covered=sum(sheet.atoms_covered for sheet in sheets),
        seed_atoms=len(configuration.positions), common_translation_rank=rank,
        shortest_common_translation=shortest)


def _grow_sheet(sheet: SheetAtlas, radius: float) -> Iterable[Tuple[Vector, str]]:
    shortest = min(math.hypot(vector[0], vector[1])
                   for vector in sheet.translations)
    extent = int(math.ceil(radius / shortest)) * 3 + 6
    for i in range(-extent, extent + 1):
        for j in range(-extent, extent + 1):
            origin = tuple(sheet.anchor[k] + i * sheet.translations[0][k] +
                           j * sheet.translations[1][k] for k in range(3))
            for offset, chemical in (((0.0, 0.0, 0.0), sheet.anchor_species),
                                     (sheet.basis_offset, sheet.basis_species)):
                point = tuple(origin[k] + offset[k] for k in range(3))
                if point[0] * point[0] + point[1] * point[1] <= radius * radius + 1e-8:
                    yield point, chemical


def grow(atlas: BilayerAtlas, radius: float, name: str = "learned-growth") -> AtomicConfiguration:
    atoms = list(atom for sheet in atlas.sheets for atom in _grow_sheet(sheet, radius))
    atoms.sort(key=lambda atom: (round(atom[0][2], 8), round(atom[0][0], 8),
                                 round(atom[0][1], 8), atom[1]))
    return AtomicConfiguration(name, tuple(atom[0] for atom in atoms),
                               tuple(atom[1] for atom in atoms),
                               provenance="generated only from the learned finite GCTS atlas")


def _score(predicted: AtomicConfiguration, target: AtomicConfiguration,
           tolerance: float = 1e-5) -> Tuple[float, float, float]:
    def key(point: Vector) -> Tuple[int, int, int]:
        return tuple(int(round(value / tolerance)) for value in point)  # type: ignore[return-value]
    target_by_position = {key(point): chemical for point, chemical in zip(
        target.positions, target.species)}
    predicted_by_position = {key(point): chemical for point, chemical in zip(
        predicted.positions, predicted.species)}
    common = set(target_by_position).intersection(predicted_by_position)
    correct = sum(target_by_position[item] == predicted_by_position[item]
                  for item in common)
    return (len(common) / max(1, len(predicted_by_position)),
            len(common) / max(1, len(target_by_position)),
            correct / max(1, len(common)))


def _classify(atlas: BilayerAtlas) -> str:
    if atlas.common_translation_rank == 2:
        if atlas.relative_pose_marking_degrees < .05:
            return "2D hexagonal crystal (aligned bilayer)"
        return "2D commensurate hexagonal moire crystal"
    if abs(atlas.relative_pose_marking_degrees - 30.0) < .05:
        return "12-fold quasiperiodic hexagonal bilayer"
    return "incommensurate hexagonal bilayer"


def evaluate_case(name: str, twist: float, seed_radius: float = 18.0,
                  heldout_radius: float = 36.0) -> MoireBenchmarkCase:
    seed = hexagonal_bilayer(name + "-seed", seed_radius, twist)
    atlas = learn_bilayer_atlas(seed)
    heldout = hexagonal_bilayer(name + "-heldout", heldout_radius, twist)
    predicted = grow(atlas, heldout_radius, name + "-predicted")
    precision, recall, chemistry = _score(predicted, heldout)
    radius_ratio = heldout_radius / seed_radius
    intrinsic_dimension = math.log(len(heldout.positions) / len(seed.positions)) / math.log(radius_ratio)
    growth = len(heldout.positions) / len(seed.positions)
    actions = max(0, math.ceil(math.log(1_000_000 / len(seed.positions), 4.0)))
    return MoireBenchmarkCase(
        name, len(seed.positions), len(heldout.positions), len(set(seed.species)),
        intrinsic_dimension, len(atlas.sheets), atlas.cluster_isometry_classes,
        atlas.cluster_pose_states, atlas.relative_pose_marking_degrees,
        atlas.common_translation_rank, atlas.shortest_common_translation,
        _classify(atlas), atlas.seed_atoms_covered / atlas.seed_atoms,
        precision, recall, chemistry, growth, actions, False, False, False)


def evaluate() -> Tuple[MoireBenchmarkCase, ...]:
    return (
        evaluate_case("hBN-aligned", 0.0),
        evaluate_case("hBN-commensurate-m2-n1", commensurate_twist(2, 1)),
        evaluate_case("hBN-30deg", math.pi / 6.0),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    if args.json:
        print(json.dumps([asdict(case) for case in result], indent=2))
    else:
        for case in result:
            print(case)


if __name__ == "__main__":
    main()
