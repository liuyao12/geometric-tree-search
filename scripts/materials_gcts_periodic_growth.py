#!/usr/bin/env python3
"""Translation-macro discovery and exact periodic growth for atomic systems.

The learner receives only positions, species, and the observed periodic cell.
It discovers color-preserving translations, groups atoms into translation
orbits (a primitive macrocluster basis), reconstructs the input, and grows an
eight-times-larger cell.  Known primitive atom counts are used only for final
evaluation, never by the discovery algorithm.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from materials_gcts_generic import (
    AtomicConfiguration,
    benchmark_systems,
    fractional_to_cartesian,
    inverse3,
    learn_catalog,
    local_descriptors,
    matvec,
    norm,
    squared_distance,
)

Fractional = Tuple[float, float, float]


@dataclass(frozen=True)
class PeriodicGrowthResult:
    system: str
    observed_atoms: int
    translation_group_size: int
    discovered_primitive_atoms: int
    reference_primitive_atoms: int
    primitive_match: bool
    reconstruction_exact: bool
    grown_atoms: int
    growth_factor: int
    original_motif_types: int
    grown_motif_types: int
    maximum_grown_motif_residual: float


REFERENCE_PRIMITIVE_ATOMS = {
    "NiAl-B2": 2,
    "Cu3Au-L12": 4,
    "GaAs-zincblende": 2,
    "NaCl-rocksalt": 2,
    "SrTiO3-perovskite": 5,
    "Cd6Yb-1/1-approximant": 84,
}


def fractional_positions(configuration: AtomicConfiguration) -> Tuple[Fractional, ...]:
    if not configuration.periodic or configuration.cell is None:
        raise ValueError("translation macros require a periodic cell")
    inverse = inverse3(configuration.cell)
    return tuple(tuple(value % 1.0 for value in matvec(inverse, position))
                 for position in configuration.positions)  # type: ignore[return-value]


def wrap_fractional(point: Sequence[float]) -> Fractional:
    return tuple(value % 1.0 for value in point)  # type: ignore[return-value]


def fractional_delta(left: Sequence[float], right: Sequence[float]) -> Fractional:
    return tuple((right[axis] - left[axis] + .5) % 1.0 - .5
                 for axis in range(3))  # type: ignore[return-value]


def point_distance(
    cell,
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    return norm(fractional_to_cartesian(cell, fractional_delta(left, right)))


def matching_index(
    configuration: AtomicConfiguration,
    fractional: Sequence[Fractional],
    point: Fractional,
    chemical: str,
    tolerance: float,
) -> int:
    assert configuration.cell is not None
    best = -1
    best_distance = math.inf
    for index, candidate in enumerate(fractional):
        if configuration.species[index] != chemical:
            continue
        distance = point_distance(configuration.cell, point, candidate)
        if distance < best_distance:
            best, best_distance = index, distance
    return best if best_distance <= tolerance else -1


def translation_is_valid(
    configuration: AtomicConfiguration,
    fractional: Sequence[Fractional],
    translation: Fractional,
    tolerance: float,
) -> bool:
    for index, point in enumerate(fractional):
        shifted = wrap_fractional(tuple(point[axis] + translation[axis]
                                        for axis in range(3)))
        if matching_index(configuration, fractional, shifted,
                          configuration.species[index], tolerance) < 0:
            return False
    return True


def translation_group(
    configuration: AtomicConfiguration,
    tolerance: float = 1e-5,
) -> Tuple[Fractional, ...]:
    fractional = fractional_positions(configuration)
    counts: Dict[str, int] = {}
    for chemical in configuration.species:
        counts[chemical] = counts.get(chemical, 0) + 1
    anchor_species = min(counts, key=lambda chemical: (counts[chemical], chemical))
    anchor = configuration.species.index(anchor_species)
    candidates: Dict[Tuple[int, int, int], Fractional] = {}
    for index, chemical in enumerate(configuration.species):
        if chemical != anchor_species:
            continue
        translation = wrap_fractional(tuple(
            fractional[index][axis] - fractional[anchor][axis]
            for axis in range(3)))
        key = tuple(round(value * 10**9) for value in translation)
        candidates[key] = translation
    valid = [
        translation for translation in candidates.values()
        if translation_is_valid(configuration, fractional, translation, tolerance)
    ]
    return tuple(sorted(valid))


def primitive_basis_indices(
    configuration: AtomicConfiguration,
    group: Sequence[Fractional],
    tolerance: float = 1e-5,
) -> Tuple[int, ...]:
    fractional = fractional_positions(configuration)
    covered: Set[int] = set()
    representatives = []
    for index, point in enumerate(fractional):
        if index in covered:
            continue
        representatives.append(index)
        for translation in group:
            shifted = wrap_fractional(tuple(point[axis] + translation[axis]
                                            for axis in range(3)))
            match = matching_index(configuration, fractional, shifted,
                                   configuration.species[index], tolerance)
            if match >= 0:
                covered.add(match)
    return tuple(representatives)


def reconstructs(
    configuration: AtomicConfiguration,
    group: Sequence[Fractional],
    representatives: Sequence[int],
    tolerance: float = 1e-5,
) -> bool:
    fractional = fractional_positions(configuration)
    generated: Set[int] = set()
    for index in representatives:
        for translation in group:
            shifted = wrap_fractional(tuple(
                fractional[index][axis] + translation[axis] for axis in range(3)))
            match = matching_index(configuration, fractional, shifted,
                                   configuration.species[index], tolerance)
            if match < 0:
                return False
            generated.add(match)
    return len(generated) == len(configuration.positions)


def replicate(
    configuration: AtomicConfiguration,
    repeats: Tuple[int, int, int] = (2, 2, 2),
) -> AtomicConfiguration:
    if configuration.cell is None:
        raise ValueError("replication requires a cell")
    positions = []
    species = []
    for image in itertools.product(*(range(value) for value in repeats)):
        shift = tuple(sum(image[axis] * configuration.cell[axis][coordinate]
                          for axis in range(3)) for coordinate in range(3))
        for point, chemical in zip(configuration.positions, configuration.species):
            positions.append(tuple(point[axis] + shift[axis] for axis in range(3)))
            species.append(chemical)
    cell = tuple(tuple(configuration.cell[axis][coordinate] * repeats[axis]
                       for coordinate in range(3)) for axis in range(3))
    return AtomicConfiguration(
        configuration.name + "-grown", tuple(positions), tuple(species),
        cell, True, configuration.provenance)


def evaluate(configuration: AtomicConfiguration) -> PeriodicGrowthResult:
    group = translation_group(configuration)
    basis = primitive_basis_indices(configuration, group)
    reconstructed = reconstructs(configuration, group, basis)
    original_descriptors = local_descriptors(configuration)
    prototypes, _, _ = learn_catalog(original_descriptors)
    grown = replicate(configuration)
    # One observed-cell image contains one representative of every replicated
    # translation orbit.  Neighborhoods are still computed against the entire
    # grown cell, including atoms across its periodic boundary.
    grown_descriptors = local_descriptors(
        grown, centers=range(len(configuration.positions)))
    grown_prototypes, _, _ = learn_catalog(grown_descriptors)
    maximum_residual = max(
        min(squared_distance(descriptor, prototype) for prototype in prototypes)
        for descriptor in grown_descriptors)
    reference = REFERENCE_PRIMITIVE_ATOMS[configuration.name]
    return PeriodicGrowthResult(
        configuration.name,
        len(configuration.positions),
        len(group),
        len(basis),
        reference,
        len(basis) == reference,
        reconstructed,
        len(grown.positions),
        len(grown.positions) // len(configuration.positions),
        len(prototypes),
        len(grown_prototypes),
        maximum_residual,
    )


def run_suite() -> Tuple[PeriodicGrowthResult, ...]:
    return tuple(evaluate(configuration) for configuration in benchmark_systems())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    results = run_suite()
    if arguments.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            print(result)


if __name__ == "__main__":
    main()
