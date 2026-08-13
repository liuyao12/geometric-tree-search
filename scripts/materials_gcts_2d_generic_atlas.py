#!/usr/bin/env python3
"""Generic finite-atlas learning for intrinsically planar atomic point sets.

Unlike ``materials_gcts_2d_moire``, this learner does not assume two sheets,
two chemical species, a two-atom motif, an XY plane, or a hexagonal family
label.  It discovers connected components, recurrent colored translations,
the complete motif modulo those translations, and symmetry-quotiented motif
isometry classes directly from a finite colored point cloud.

The fixture generator remains hexagonal because moire materials are the first
benchmark target.  Generator indices, basis coordinates, twist angles, and
held-out atoms are never passed to the learner.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from materials_gcts_generic import AtomicConfiguration

Vector = Tuple[float, float, float]
Site = Tuple[int, int, int]
BasisAtom = Tuple[float, float, float, str]


@dataclass(frozen=True)
class MotifAtom:
    offset: Vector
    species: str
    observations: int


@dataclass(frozen=True)
class PlanarComponentAtlas:
    origin: Vector
    translations: Tuple[Vector, Vector]
    normal: Vector
    motif: Tuple[MotifAtom, ...]
    atoms_covered: int
    translation_support: Tuple[float, float]
    motif_isometry_class: int


@dataclass(frozen=True)
class GenericPlanarAtlas:
    components: Tuple[PlanarComponentAtlas, ...]
    seed_atoms: int
    seed_atoms_covered: int
    motif_isometry_classes: int
    pose_states: int
    observation_center: Vector


@dataclass(frozen=True)
class GenericPlanarCase:
    system: str
    seed_atoms: int
    heldout_atoms: int
    species_count: int
    learned_components: int
    learned_motif_atoms: Tuple[int, ...]
    motif_isometry_classes: int
    pose_states: int
    seed_cover_fraction: float
    inferred_intrinsic_dimension: float
    heldout_position_precision: float
    heldout_position_recall: float
    heldout_chemical_accuracy: float
    pose_marking_ablation_recall: float
    flat_seed_only_recall: float
    marked_recall_gain: float
    new_atoms_generated: int
    macro_pose_actions: int
    atoms_per_macro_pose_action: float
    atomic_decisions_avoided: int
    arbitrary_global_rotation_applied: bool
    target_atoms_used_for_learning: bool
    generator_indices_used_for_learning: bool
    physical_potential_used: bool


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(left[k] + right[k] for k in range(3))  # type: ignore[return-value]


def _sub(left: Vector, right: Vector) -> Vector:
    return tuple(left[k] - right[k] for k in range(3))  # type: ignore[return-value]


def _scale(vector: Vector, scalar: float) -> Vector:
    return tuple(value * scalar for value in vector)  # type: ignore[return-value]


def _dot(left: Vector, right: Vector) -> float:
    return sum(left[k] * right[k] for k in range(3))


def _cross(left: Vector, right: Vector) -> Vector:
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def _norm(vector: Vector) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector: Vector) -> Vector:
    length = _norm(vector)
    if length < 1e-12:
        raise ValueError("cannot normalize a zero vector")
    return _scale(vector, 1.0 / length)


def _key(point: Vector, tolerance: float) -> Site:
    return tuple(int(round(value / tolerance)) for value in point)  # type: ignore[return-value]


def _rotation_matrix() -> Tuple[Vector, Vector, Vector]:
    """A fixed proper rotation with no coordinate plane left invariant."""
    axis = _unit((1.0, 2.0, -1.5))
    angle = .731
    cosine, sine = math.cos(angle), math.sin(angle)
    x, y, z = axis
    return (
        (cosine + x * x * (1 - cosine),
         x * y * (1 - cosine) - z * sine,
         x * z * (1 - cosine) + y * sine),
        (y * x * (1 - cosine) + z * sine,
         cosine + y * y * (1 - cosine),
         y * z * (1 - cosine) - x * sine),
        (z * x * (1 - cosine) - y * sine,
         z * y * (1 - cosine) + x * sine,
         cosine + z * z * (1 - cosine)),
    )


def _matvec(matrix: Sequence[Sequence[float]], vector: Vector) -> Vector:
    return tuple(sum(matrix[row][column] * vector[column]
                     for column in range(3)) for row in range(3))  # type: ignore[return-value]


def rotate_configuration(configuration: AtomicConfiguration) -> AtomicConfiguration:
    matrix = _rotation_matrix()
    return AtomicConfiguration(
        configuration.name + "-globally-rotated",
        tuple(_matvec(matrix, point) for point in configuration.positions),
        configuration.species, provenance=configuration.provenance +
        "; fixed proper global rotation applied")


def layered_hexagonal_configuration(
    name: str,
    radius: float,
    sheet_basis: Sequence[BasisAtom],
    sheet_angles: Sequence[float],
    lattice_constant: float = 2.50,
    sheet_separation: float = 7.0,
    global_rotation: bool = False,
) -> AtomicConfiguration:
    """Generate finite periodic sheets with an arbitrary colored 3D motif.

    ``sheet_basis`` entries are fractional coordinates along the two triangular
    Bravais vectors, a normal offset, and a species label.  This metadata is
    fixture-only and is discarded in the returned configuration.
    """
    a1 = (lattice_constant, 0.0)
    a2 = (.5 * lattice_constant, .5 * math.sqrt(3.0) * lattice_constant)
    extent = int(math.ceil(radius / lattice_constant)) + 5
    positions: List[Vector] = []
    species: List[str] = []
    sheet_midpoint = .5 * (len(sheet_angles) - 1)
    for sheet_index, angle in enumerate(sheet_angles):
        cosine, sine = math.cos(angle), math.sin(angle)
        sheet_z = (sheet_index - sheet_midpoint) * sheet_separation
        for i in range(-extent, extent + 1):
            for j in range(-extent, extent + 1):
                for fraction1, fraction2, normal_offset, chemical in sheet_basis:
                    x = (i + fraction1) * a1[0] + (j + fraction2) * a2[0]
                    y = (i + fraction1) * a1[1] + (j + fraction2) * a2[1]
                    rotated = (cosine * x - sine * y,
                               sine * x + cosine * y)
                    if rotated[0] ** 2 + rotated[1] ** 2 <= radius ** 2 + 1e-9:
                        positions.append((rotated[0], rotated[1],
                                          sheet_z + normal_offset))
                        species.append(chemical)
    order = sorted(range(len(positions)), key=lambda index: (
        round(positions[index][2], 8), round(positions[index][0], 8),
        round(positions[index][1], 8), species[index]))
    configuration = AtomicConfiguration(
        name, tuple(positions[index] for index in order),
        tuple(species[index] for index in order), provenance=(
            "synthetic finite layered hexagonal fixture; indices and basis "
            "coordinates discarded before learning"))
    return rotate_configuration(configuration) if global_rotation else configuration


def _components(configuration: AtomicConfiguration) -> Tuple[Tuple[int, ...], ...]:
    points = configuration.positions
    nearest = min(_norm(_sub(left, right)) for index, left in enumerate(points)
                  for right in points[index + 1:] if _norm(_sub(left, right)) > 1e-8)
    # Use the second-shell bridge as well as the shortest bond.  A first-shell
    # graph fragments around vacancies; the wider finite cutoff still remains
    # well below the separated-sheet fixtures and is inferred from the cloud's
    # own shortest distance rather than a material label.
    cutoff = nearest * 1.72
    adjacency = [[] for _ in points]
    for first, left in enumerate(points):
        for second in range(first + 1, len(points)):
            if _norm(_sub(left, points[second])) <= cutoff:
                adjacency[first].append(second)
                adjacency[second].append(first)
    unseen = set(range(len(points)))
    result = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        stack = [root]
        component = []
        while stack:
            current = stack.pop()
            component.append(current)
            for other in adjacency[current]:
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
        result.append(tuple(sorted(component)))
    return tuple(sorted(result, key=lambda component: (-len(component), component[0])))


def _translation_candidates(
    configuration: AtomicConfiguration,
    indices: Sequence[int],
    tolerance: float,
) -> Tuple[Tuple[Vector, float], ...]:
    """Find short colored translations with majority support in a component."""
    counts: Dict[Site, int] = collections.Counter()
    vector_sums: Dict[Site, List[float]] = collections.defaultdict(
        lambda: [0.0, 0.0, 0.0])
    species_groups: Dict[str, List[int]] = collections.defaultdict(list)
    for index in indices:
        species_groups[configuration.species[index]].append(index)
    for group in species_groups.values():
        for position, first in enumerate(group):
            for second in group[position + 1:]:
                vector = _sub(configuration.positions[second],
                              configuration.positions[first])
                for signed in (vector, _scale(vector, -1.0)):
                    key = _key(signed, tolerance)
                    counts[key] += 1
                    for axis in range(3):
                        vector_sums[key][axis] += signed[axis]
    candidates = []
    for key, _ in counts.most_common(768):
        neighborhood = tuple(
            (key[0] + dx, key[1] + dy, key[2] + dz)
            for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            for dz in (-1, 0, 1))
        support = sum(counts[neighbor] for neighbor in neighborhood)
        fraction = support / len(indices)
        if fraction < .55:
            continue
        vector = tuple(sum(vector_sums[neighbor][axis]
                           for neighbor in neighborhood) / support
                       for axis in range(3))
        candidates.append((vector, fraction))
    deduplicated = []
    for vector, fraction in sorted(candidates, key=lambda item: (
            _norm(item[0]), -item[1], item[0])):
        if any(_norm(_sub(vector, previous[0])) <= tolerance * 2.0
               for previous in deduplicated):
            continue
        deduplicated.append((vector, fraction))
    return tuple(deduplicated)


def _translation_basis(
    configuration: AtomicConfiguration,
    indices: Sequence[int],
    tolerance: float,
) -> Tuple[Tuple[Vector, Vector], Tuple[float, float]]:
    candidates = _translation_candidates(configuration, indices, tolerance)
    if not candidates:
        raise ValueError("no majority-supported colored translation")
    first, first_support = candidates[0]
    for second, second_support in candidates[1:]:
        if _norm(_cross(first, second)) > .25 * _norm(first) * _norm(second):
            return (first, second), (first_support, second_support)
    raise ValueError("supported translations have rank below two")


def _lattice_coordinates(vector: Vector, first: Vector,
                         second: Vector) -> Tuple[float, float]:
    g11, g12, g22 = _dot(first, first), _dot(first, second), _dot(second, second)
    determinant = g11 * g22 - g12 * g12
    if determinant < 1e-12:
        raise ValueError("singular translation basis")
    rhs1, rhs2 = _dot(vector, first), _dot(vector, second)
    return ((rhs1 * g22 - rhs2 * g12) / determinant,
            (rhs2 * g11 - rhs1 * g12) / determinant)


def _canonical_fraction(value: float, tolerance: float = 1e-7) -> float:
    fraction = value - math.floor(value)
    return 0.0 if fraction < tolerance or 1.0 - fraction < tolerance else fraction


def _periodic_delta(left: Vector, right: Vector,
                    first: Vector, second: Vector) -> Vector:
    """Shortest difference between motif residues modulo two translations."""
    best = _sub(left, right)
    best_length = _norm(best)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            candidate = _sub(left, _add(right, _add(_scale(first, i),
                                                    _scale(second, j))))
            length = _norm(candidate)
            if length < best_length:
                best, best_length = candidate, length
    return best


def _cluster_motif_residues(
    observations: Sequence[Tuple[Vector, str]],
    first: Vector,
    second: Vector,
    threshold: float,
) -> Tuple[MotifAtom, ...]:
    """Tolerance-cover motif observations on the learned translation torus."""
    clusters: List[Tuple[str, List[Vector]]] = []
    for residue, chemical in observations:
        best_index: Optional[int] = None
        best_delta: Optional[Vector] = None
        best_length = float("inf")
        for index, (cluster_species, members) in enumerate(clusters):
            if cluster_species != chemical:
                continue
            prototype = tuple(sum(point[axis] for point in members) / len(members)
                              for axis in range(3))
            delta = _periodic_delta(residue, prototype, first, second)
            length = _norm(delta)
            if length < threshold and length < best_length:
                best_index, best_delta, best_length = index, delta, length
        if best_index is None:
            clusters.append((chemical, [residue]))
        else:
            chemical0, members = clusters[best_index]
            prototype = tuple(sum(point[axis] for point in members) / len(members)
                              for axis in range(3))
            assert best_delta is not None
            members.append(_add(prototype, best_delta))
            clusters[best_index] = (chemical0, members)
    motif = []
    for chemical, members in clusters:
        offset = tuple(sum(point[axis] for point in members) / len(members)
                       for axis in range(3))
        motif.append(MotifAtom(offset, chemical, len(members)))
    return tuple(sorted(motif, key=lambda atom: (atom.species,
                                                 tuple(round(x, 8)
                                                       for x in atom.offset))))


def _learn_component(
    configuration: AtomicConfiguration,
    indices: Sequence[int],
    tolerance: float,
) -> PlanarComponentAtlas:
    translations, support = _translation_basis(configuration, indices, tolerance)
    first, second = translations
    normal = _unit(_cross(first, second))
    center = tuple(sum(configuration.positions[index][axis] for index in indices)
                   / len(indices) for axis in range(3))
    origin_index = min(indices, key=lambda index: _norm(
        _sub(configuration.positions[index], center)))
    origin = configuration.positions[origin_index]
    residues: List[Tuple[Vector, str]] = []
    for index in indices:
        delta = _sub(configuration.positions[index], origin)
        coordinate1, coordinate2 = _lattice_coordinates(delta, first, second)
        fraction1 = _canonical_fraction(coordinate1)
        fraction2 = _canonical_fraction(coordinate2)
        planar = _add(_scale(first, fraction1), _scale(second, fraction2))
        normal_part = _scale(normal, _dot(delta, normal))
        residue = _add(planar, normal_part)
        residues.append((residue, configuration.species[index]))
    motif_threshold = max(tolerance * 8.0,
                          .06 * min(_norm(first), _norm(second)))
    motif = _cluster_motif_residues(residues, first, second, motif_threshold)
    return PlanarComponentAtlas(origin, translations, normal, motif,
                                len(indices), support, -1)


def _motif_fingerprint(component: PlanarComponentAtlas) -> Tuple:
    atoms = component.motif
    distances = []
    for first, left in enumerate(atoms):
        for right in atoms[first + 1:]:
            pair = tuple(sorted((left.species, right.species)))
            distances.append((pair, round(_norm(_periodic_delta(
                left.offset, right.offset, component.translations[0],
                component.translations[1])), 2)))
    length1, length2 = (_norm(component.translations[0]),
                        _norm(component.translations[1]))
    gram = (round(.5 * (length1 + length2), 1),
            round(min(length1, length2) / max(length1, length2), 2),
            round(abs(_dot(component.translations[0],
                           component.translations[1])) /
                  (length1 * length2), 2))
    return (tuple(sorted(atom.species for atom in atoms)),
            tuple(sorted(distances)), gram)


def learn_planar_atlas(
    configuration: AtomicConfiguration,
    observation_center: Vector = (0.0, 0.0, 0.0),
    tolerance: float = 2e-5,
) -> GenericPlanarAtlas:
    raw_components = _components(configuration)
    components = [list(component) for component in raw_components
                  if len(component) >= 8]
    residual = [index for component in raw_components if len(component) < 8
                for index in component]
    provisional = [_learn_component(configuration, component, tolerance)
                   for component in components]
    # Vacancies can isolate a few surviving atoms from a bonded component.
    # Assign those residual atoms to the nearest learned affine sheet and then
    # refit.  This is also the explicit "gap cluster" path: no seed atom is
    # silently discarded merely because its local graph is incomplete.
    for index in residual:
        point = configuration.positions[index]
        selected = min(range(len(provisional)), key=lambda component_index: abs(
            _dot(_sub(point, provisional[component_index].origin),
                 provisional[component_index].normal)))
        components[selected].append(index)
    learned = [_learn_component(configuration, component, tolerance)
               for component in components]
    classes: Dict[Tuple, int] = {}
    typed = []
    for component in learned:
        fingerprint = _motif_fingerprint(component)
        class_index = classes.setdefault(fingerprint, len(classes))
        typed.append(PlanarComponentAtlas(
            component.origin, component.translations, component.normal,
            component.motif, component.atoms_covered,
            component.translation_support, class_index))
    covered = sum(component.atoms_covered for component in typed)
    if covered != len(configuration.positions):
        raise ValueError("learned planar components do not cover every seed atom")
    return GenericPlanarAtlas(tuple(typed), len(configuration.positions), covered,
                              len(classes), len(typed), observation_center)


def _grow_component(component: PlanarComponentAtlas, center: Vector,
                    radius: float) -> Iterable[Tuple[Vector, str]]:
    shortest = min(_norm(vector) for vector in component.translations)
    extent = int(math.ceil(radius / shortest)) * 3 + 8
    for i in range(-extent, extent + 1):
        for j in range(-extent, extent + 1):
            lattice = _add(_scale(component.translations[0], i),
                           _scale(component.translations[1], j))
            for motif_atom in component.motif:
                point = _add(component.origin, _add(lattice, motif_atom.offset))
                delta = _sub(point, center)
                in_plane = _sub(delta, _scale(component.normal,
                                              _dot(delta, component.normal)))
                if _norm(in_plane) <= radius + 1e-7:
                    yield point, motif_atom.species


def grow(
    atlas: GenericPlanarAtlas,
    radius: float,
    retain_one_pose_per_isometry_class: bool = False,
) -> AtomicConfiguration:
    components = atlas.components
    if retain_one_pose_per_isometry_class:
        seen = set()
        components = tuple(component for component in components
                           if component.motif_isometry_class not in seen
                           and not seen.add(component.motif_isometry_class))
    atoms = [atom for component in components for atom in _grow_component(
        component, atlas.observation_center, radius)]
    atoms.sort(key=lambda atom: (_key(atom[0], 1e-7), atom[1]))
    return AtomicConfiguration(
        "generic-planar-atlas-growth", tuple(atom[0] for atom in atoms),
        tuple(atom[1] for atom in atoms), provenance=(
            "generated from learned colored motifs, translation ports, and "
            "component pose markings only"))


def _score(predicted: AtomicConfiguration, target: AtomicConfiguration,
           tolerance: float = 4e-5) -> Tuple[float, float, float]:
    target_by_position = {_key(point, tolerance): chemical
                          for point, chemical in zip(target.positions, target.species)}
    predicted_by_position = {_key(point, tolerance): chemical
                             for point, chemical in zip(predicted.positions,
                                                       predicted.species)}
    common = set(target_by_position).intersection(predicted_by_position)
    correct = sum(target_by_position[key] == predicted_by_position[key]
                  for key in common)
    return (len(common) / max(1, len(predicted_by_position)),
            len(common) / max(1, len(target_by_position)),
            correct / max(1, len(common)))


def evaluate_case(
    name: str,
    basis: Sequence[BasisAtom],
    angles: Sequence[float],
    global_rotation: bool,
    seed_radius: float = 18.0,
    heldout_radius: float = 36.0,
) -> GenericPlanarCase:
    seed = layered_hexagonal_configuration(
        name + "-seed", seed_radius, basis, angles,
        global_rotation=global_rotation)
    atlas = learn_planar_atlas(seed)
    heldout = layered_hexagonal_configuration(
        name + "-heldout", heldout_radius, basis, angles,
        global_rotation=global_rotation)
    predicted = grow(atlas, heldout_radius)
    precision, recall, chemistry = _score(predicted, heldout)
    ablated = grow(atlas, heldout_radius,
                   retain_one_pose_per_isometry_class=True)
    _, ablated_recall, _ = _score(ablated, heldout)
    flat_recall = len(seed.positions) / len(heldout.positions)
    dimension = math.log(len(heldout.positions) / len(seed.positions), 2.0)
    new_atoms = len(heldout.positions) - len(seed.positions)
    macro_actions = len(atlas.components)
    return GenericPlanarCase(
        name, len(seed.positions), len(heldout.positions), len(set(seed.species)),
        len(atlas.components), tuple(len(component.motif)
                                     for component in atlas.components),
        atlas.motif_isometry_classes, atlas.pose_states,
        atlas.seed_atoms_covered / atlas.seed_atoms, dimension,
        precision, recall, chemistry, ablated_recall, flat_recall,
        recall - ablated_recall, new_atoms, macro_actions,
        new_atoms / macro_actions, new_atoms - macro_actions,
        global_rotation, False, False, False)


def evaluate() -> Tuple[GenericPlanarCase, ...]:
    hbn = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    graphene = ((0.0, 0.0, 0.0, "C"),
                (1 / 3, 1 / 3, 0.0, "C"))
    janus = ((0.0, 0.0, 0.0, "Mo"),
             (1 / 3, 1 / 3, 1.56, "S"),
             (1 / 3, 1 / 3, -1.68, "Se"))
    return (
        evaluate_case("graphene-monolayer", graphene, (0.0,), True),
        evaluate_case("hBN-30deg-bilayer", hbn, (0.0, math.pi / 6), True),
        evaluate_case("Janus-MoSSe-13deg-bilayer", janus,
                      (0.0, math.radians(13.0)), True,
                      seed_radius=16.0, heldout_radius=32.0),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps([asdict(case) for case in result], indent=2)
          if args.json else "\n".join(map(str, result)))


if __name__ == "__main__":
    main()
