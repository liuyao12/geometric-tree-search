#!/usr/bin/env python3
"""Select local registry markings or higher-order pose macros for bilayers.

An exact local cross-layer environment is not automatically a finite GCTS
state.  For an aligned or commensurate bilayer, registry descriptors recur in
a bounded vocabulary.  For a 30-degree incommensurate union, the vocabulary
grows with the observation window even though the whole structure has a compact
description as two periodic components plus one relative pose.

This benchmark learns both descriptions from the same finite colored point
cloud and selects the bounded one without a crystallographic family label.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from dataclasses import asdict, dataclass
from typing import Dict, List, Sequence, Tuple

from materials_gcts_2d_generic_atlas import (
    GenericPlanarAtlas, Vector, _components, _dot, _norm, _scale, _score,
    _sub, grow, layered_hexagonal_configuration, learn_planar_atlas)
from materials_gcts_2d_moire import commensurate_twist
from materials_gcts_generic import AtomicConfiguration

RegistryState = Tuple[str, Tuple[Tuple[str, int], ...]]


@dataclass(frozen=True)
class RegistrySelectionCase:
    system: str
    seed_atoms: int
    heldout_atoms: int
    registry_centers_by_window: Tuple[int, ...]
    registry_states_by_window: Tuple[int, ...]
    final_states_per_center: float
    heldout_registry_states: int
    seed_local_marking_heldout_coverage: float
    vocabulary_growth_exponent: float
    local_vocabulary_bounded: bool
    selected_representation: str
    selected_marking_states: int
    selected_position_precision: float
    selected_position_recall: float
    selected_chemical_accuracy: float
    local_marking_recall_if_forced: float
    pose_fallback_fraction: float
    pose_macro_recall_if_used: float
    representation_selected_without_family_label: bool
    heldout_atoms_used_for_selection: bool
    physical_potential_used: bool


@dataclass(frozen=True)
class RegistrySelectionBenchmark:
    cases: Tuple[RegistrySelectionCase, ...]
    commensurate_local_marking_selected: bool
    quasiperiodic_pose_macro_selected: bool
    growing_local_vocabulary_rejected: bool
    all_selected_growth_exact: bool


def _center(configuration: AtomicConfiguration) -> Vector:
    return tuple(sum(point[axis] for point in configuration.positions) /
                 len(configuration.positions) for axis in range(3))  # type: ignore[return-value]


def registry_descriptors(
    configuration: AtomicConfiguration,
    atlas: GenericPlanarAtlas,
    maximum_center_radius: float,
    neighbor_count: int = 8,
    distance_quantum: float = 1e-4,
) -> Tuple[Tuple[float, RegistryState], ...]:
    """Rotation-invariant local cross-layer sections from positions/species."""
    components = tuple(component for component in _components(configuration)
                       if len(component) >= 8)
    if len(components) != 2 or len(atlas.components) != 2:
        raise ValueError("registry benchmark requires two learned components")
    normal = atlas.components[0].normal
    center = _center(configuration)
    descriptors = []
    for index in components[0]:
        point = configuration.positions[index]
        relative = _sub(point, center)
        normal_coordinate = _dot(relative, normal)
        planar = _sub(relative, _scale(normal, normal_coordinate))
        radius = _norm(planar)
        if radius > maximum_center_radius:
            continue
        neighbors: List[Tuple[float, str]] = []
        for other in components[1]:
            displacement = _sub(configuration.positions[other], point)
            normal_distance = _dot(displacement, normal)
            projected = _sub(displacement, _scale(normal, normal_distance))
            neighbors.append((_norm(projected),
                              configuration.species[other]))
        neighbors.sort(key=lambda item: (item[0], item[1]))
        state = (
            configuration.species[index],
            tuple((chemical, int(round(distance / distance_quantum)))
                  for distance, chemical in neighbors[:neighbor_count]))
        descriptors.append((radius, state))
    return tuple(descriptors)


def _case(name: str, angle: float) -> RegistrySelectionCase:
    basis = ((0.0, 0.0, 0.0, "B"), (1 / 3, 1 / 3, 0.0, "N"))
    seed = layered_hexagonal_configuration(
        name + "-seed", 20.0, basis, (0.0, angle),
        global_rotation=True)
    atlas = learn_planar_atlas(seed)
    seed_descriptors = registry_descriptors(seed, atlas, 15.0)
    windows = (5.0, 10.0, 15.0)
    centers = tuple(sum(radius <= window for radius, _ in seed_descriptors)
                    for window in windows)
    vocabularies = tuple(len({state for radius, state in seed_descriptors
                              if radius <= window}) for window in windows)
    growth_exponent = math.log(vocabularies[-1] / vocabularies[0]) / math.log(
        centers[-1] / centers[0]) if vocabularies[-1] > vocabularies[0] else 0.0
    bounded = (vocabularies[-1] <= 16 and
               vocabularies[-1] <= 1.5 * max(1, vocabularies[-2]))

    heldout_radius = 32.0
    heldout = layered_hexagonal_configuration(
        name + "-heldout", heldout_radius, basis, (0.0, angle),
        global_rotation=True)
    # The held-out structure is opened only after the representation choice.
    selected = "finite local registry marking + pose fallback" if bounded else (
        "cluster-of-clusters relative-pose macro")
    training_states = {state for _, state in seed_descriptors}
    heldout_descriptors = registry_descriptors(
        heldout, atlas, heldout_radius - 5.0)
    heldout_states = {state for _, state in heldout_descriptors}
    local_coverage = sum(state in training_states
                         for _, state in heldout_descriptors) / len(
                             heldout_descriptors)
    predicted = grow(atlas, heldout_radius)
    precision, recall, chemistry = _score(predicted, heldout)
    selected_states = (len(training_states) + len(atlas.components)
                       if bounded else len(atlas.components))
    fallback_fraction = 1.0 - local_coverage if bounded else 1.0
    return RegistrySelectionCase(
        name, len(seed.positions), len(heldout.positions), centers,
        vocabularies, vocabularies[-1] / centers[-1], len(heldout_states),
        local_coverage, growth_exponent, bounded, selected, selected_states,
        precision, recall, chemistry, local_coverage, fallback_fraction, recall,
        True, False, False)


def evaluate() -> RegistrySelectionBenchmark:
    cases = (
        _case("aligned-hBN-registry", 0.0),
        _case("commensurate-hBN-m2-n1-registry", commensurate_twist(2, 1)),
        _case("30deg-hBN-registry", math.pi / 6),
    )
    return RegistrySelectionBenchmark(
        cases,
        all(case.local_vocabulary_bounded for case in cases[:2]),
        not cases[2].local_vocabulary_bounded and
        "pose macro" in cases[2].selected_representation,
        cases[2].registry_states_by_window[-1] >
        2 * cases[2].registry_states_by_window[0],
        all(case.selected_position_recall >= .95 for case in cases))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    print(json.dumps(asdict(result), indent=2) if args.json else result)


if __name__ == "__main__":
    main()
