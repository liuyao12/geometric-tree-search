#!/usr/bin/env python3
"""Recursive cluster-of-clusters address macros for generic planar GCTS.

The planar atlas first learns colored motifs, two translation ports, and pose
states from a finite disk.  This module promotes those ports into a dimension-
agnostic binary address grammar:

    M(l+1) = M(l) + (2^l,0)M(l) + (0,2^l)M(l)
             + (2^l,2^l)M(l).

The four references are cluster-of-clusters children, not copied atoms.  One
node definition therefore represents 4^l motif occurrences.  Explicit output
remains linear and is independently checked against a larger fixture disk.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Iterable, List, Tuple

from materials_gcts_2d_generic_atlas import (
    GenericPlanarAtlas, PlanarComponentAtlas, Vector, _add, _scale, _score,
    grow, layered_hexagonal_configuration, learn_planar_atlas)
from materials_gcts_generic import AtomicConfiguration


@dataclass(frozen=True)
class RecursivePlanarBenchmark:
    system: str
    seed_atoms: int
    heldout_atoms: int
    motif_atoms_per_pose: int
    pose_states: int
    child_references_per_macro: int
    learned_address_dimensions: int
    explicit_level: int
    explicit_position_precision: float
    explicit_position_recall: float
    explicit_chemical_accuracy: float
    explicit_atoms_emitted: int
    implicit_level: int
    implicit_represented_atoms: int
    seed_equivalent_level: int
    promoted_actions_seed_to_million: int
    flat_motif_actions_to_million: int
    recursive_action_reduction: float
    pose_marking_ablation_recall: float
    hierarchy_definitions: int
    explicit_output_is_linear: bool
    heldout_atoms_used_for_learning: bool
    generator_indices_used_for_learning: bool
    physical_potential_used: bool


def centered_addresses(level: int) -> Iterable[Tuple[int, int]]:
    """Expand the recursive four-child node only for explicit verification."""
    if level < 0:
        raise ValueError("level must be nonnegative")
    half = 1 << max(0, level - 1)
    lower, upper = ((0, 1) if level == 0 else (-half, half))
    for first in range(lower, upper):
        for second in range(lower, upper):
            yield first, second


def _expand_component(
    component: PlanarComponentAtlas,
    level: int,
    center: Vector,
    radius: float,
) -> Iterable[Tuple[Vector, str]]:
    for first_address, second_address in centered_addresses(level):
        translation = _add(
            _scale(component.translations[0], first_address),
            _scale(component.translations[1], second_address))
        for motif_atom in component.motif:
            point = _add(component.origin,
                         _add(translation, motif_atom.offset))
            delta = tuple(point[axis] - center[axis] for axis in range(3))
            normal_coordinate = sum(delta[axis] * component.normal[axis]
                                    for axis in range(3))
            planar = tuple(delta[axis] - normal_coordinate *
                           component.normal[axis] for axis in range(3))
            if math.sqrt(sum(value * value for value in planar)) <= radius + 1e-7:
                yield point, motif_atom.species


def expand_level(atlas: GenericPlanarAtlas, level: int,
                 radius: float, ablate_pose: bool = False
                 ) -> AtomicConfiguration:
    components = atlas.components
    if ablate_pose:
        seen = set()
        components = tuple(component for component in components
                           if component.motif_isometry_class not in seen
                           and not seen.add(component.motif_isometry_class))
    atoms: List[Tuple[Vector, str]] = []
    for component in components:
        atoms.extend(_expand_component(component, level,
                                       atlas.observation_center, radius))
    atoms.sort(key=lambda atom: (tuple(round(value, 8)
                                      for value in atom[0]), atom[1]))
    return AtomicConfiguration(
        f"recursive-planar-level-{level}",
        tuple(atom[0] for atom in atoms), tuple(atom[1] for atom in atoms),
        provenance="explicit expansion of learned four-child address macros")


def _minimum_explicit_level(atlas: GenericPlanarAtlas, radius: float) -> int:
    for level in range(1, 16):
        # A cheap containment check precedes the authoritative target score.
        half = 1 << (level - 1)
        shortest = min(math.sqrt(sum(value * value for value in translation))
                       for component in atlas.components
                       for translation in component.translations)
        if half * shortest >= 1.8 * radius:
            return level
    raise RuntimeError("no bounded explicit level contains the target disk")


def evaluate() -> RecursivePlanarBenchmark:
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    angles = (0.0, math.pi / 6)
    seed = layered_hexagonal_configuration(
        "recursive-hBN-seed", 18.0, basis, angles,
        global_rotation=True)
    atlas = learn_planar_atlas(seed)
    target_radius = 36.0
    target = layered_hexagonal_configuration(
        "recursive-hBN-heldout", target_radius, basis, angles,
        global_rotation=True)
    explicit_level = _minimum_explicit_level(atlas, target_radius)
    predicted = expand_level(atlas, explicit_level, target_radius)
    precision, recall, chemistry = _score(predicted, target)
    ablated = expand_level(atlas, explicit_level, target_radius,
                           ablate_pose=True)
    _, ablated_recall, _ = _score(ablated, target)
    motif_atoms = len(atlas.components[0].motif)
    poses = len(atlas.components)
    implicit_level = math.ceil(math.log(1_000_000 /
                                        (motif_atoms * poses), 4.0))
    represented = motif_atoms * poses * 4 ** implicit_level
    seed_level = math.ceil(math.log(len(seed.positions) /
                                    (motif_atoms * poses), 4.0))
    promoted_actions = implicit_level - seed_level
    flat_actions = math.ceil((1_000_000 - len(seed.positions)) / motif_atoms)
    return RecursivePlanarBenchmark(
        "generic-30deg-hBN-address-macro", len(seed.positions),
        len(target.positions), motif_atoms, poses, 4, 2,
        explicit_level, precision, recall, chemistry,
        len(predicted.positions), implicit_level, represented,
        seed_level, promoted_actions, flat_actions,
        flat_actions / promoted_actions, ablated_recall,
        implicit_level + 1, True, False, False, False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
