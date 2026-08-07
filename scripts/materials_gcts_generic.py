#!/usr/bin/env python3
"""Generic atomic point-cloud representation and local GCTS atlas experiments.

The code deliberately contains no lattice-specific logic.  A configuration is
positions, chemical species, and an optional periodic cell.  Local descriptors
use only species, distances, and bond angles, so they are invariant to global
translation and rotation.  The material constructors are benchmark fixtures;
the learner never sees their crystallographic labels.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

Vector = Tuple[float, float, float]
Matrix = Tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class AtomicConfiguration:
    name: str
    positions: Tuple[Vector, ...]
    species: Tuple[str, ...]
    cell: Optional[Matrix] = None
    periodic: bool = False
    provenance: str = ""

    def __post_init__(self) -> None:
        if len(self.positions) != len(self.species):
            raise ValueError("positions and species must have equal length")
        if self.periodic and self.cell is None:
            raise ValueError("periodic configurations require a cell")


@dataclass(frozen=True)
class AtlasResult:
    system: str
    atoms: int
    chemical_species: int
    motif_types: int
    compression: float
    clean_reconstruction_error: float
    noisy_type_stability: float
    rotation_type_stability: float
    fixed_k_motif_types: int
    fixed_k_noisy_stability: float


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: Vector) -> float:
    return math.sqrt(dot(a, a))


def inverse3(matrix: Matrix) -> Matrix:
    a, b, c = matrix
    determinant = dot(a, (b[1] * c[2] - b[2] * c[1],
                          b[2] * c[0] - b[0] * c[2],
                          b[0] * c[1] - b[1] * c[0]))
    if abs(determinant) < 1e-12:
        raise ValueError("singular cell")
    return (
        ((b[1] * c[2] - b[2] * c[1]) / determinant,
         (a[2] * c[1] - a[1] * c[2]) / determinant,
         (a[1] * b[2] - a[2] * b[1]) / determinant),
        ((b[2] * c[0] - b[0] * c[2]) / determinant,
         (a[0] * c[2] - a[2] * c[0]) / determinant,
         (a[2] * b[0] - a[0] * b[2]) / determinant),
        ((b[0] * c[1] - b[1] * c[0]) / determinant,
         (a[1] * c[0] - a[0] * c[1]) / determinant,
         (a[0] * b[1] - a[1] * b[0]) / determinant),
    )


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    return tuple(dot(row, vector) for row in matrix)  # type: ignore[return-value]


def fractional_to_cartesian(cell: Matrix, fractional: Vector) -> Vector:
    return tuple(sum(fractional[j] * cell[j][i] for j in range(3))
                 for i in range(3))  # type: ignore[return-value]


def displacement(
    configuration: AtomicConfiguration,
    i: int,
    j: int,
    inverse_cell: Optional[Matrix] = None,
) -> Vector:
    delta = tuple(configuration.positions[j][axis] -
                  configuration.positions[i][axis] for axis in range(3))
    if not configuration.periodic:
        return delta  # type: ignore[return-value]
    assert configuration.cell is not None
    fractional = matvec(inverse_cell or inverse3(configuration.cell), delta)
    wrapped = tuple(value - round(value) for value in fractional)
    return fractional_to_cartesian(configuration.cell, wrapped)  # type: ignore[arg-type]


def local_descriptors(
    configuration: AtomicConfiguration,
    neighbor_count: int = 12,
    close_shell: bool = True,
    centers: Optional[Sequence[int]] = None,
) -> Tuple[Tuple[float, ...], ...]:
    """Smooth invariant descriptors with species-resolved radial/angular bins."""
    names = sorted(set(configuration.species))
    species_index = {name: index for index, name in enumerate(names)}
    descriptors: List[Tuple[float, ...]] = []
    inverse_cell = (inverse3(configuration.cell)
                    if configuration.periodic and configuration.cell else None)
    radial_bins = 8
    angular_bins = 8
    selected_centers = (range(len(configuration.positions))
                        if centers is None else centers)
    for center in selected_centers:
        neighbors = []
        for other in range(len(configuration.positions)):
            if other == center:
                continue
            vector = displacement(configuration, center, other, inverse_cell)
            distance = norm(vector)
            if distance > 1e-10:
                neighbors.append((distance, configuration.species[other], vector))
        neighbors.sort(key=lambda item: (item[0], item[1]))
        # Never cut a crystallographic coordination shell merely because it
        # straddles the nominal k-nearest-neighbor boundary.  A small relative
        # band also makes the decision stable under thermal displacement.
        nominal = min(neighbor_count, len(neighbors))
        cutoff = neighbors[nominal - 1][0] * 1.05 if nominal else 0.0
        selected = ([item for item in neighbors if item[0] <= cutoff]
                    if close_shell else neighbors[:nominal])
        scale = selected[0][0] if selected else 1.0
        center_one_hot = [0.0] * len(names)
        center_one_hot[species_index[configuration.species[center]]] = 1.0
        radial = [0.0] * (len(names) * radial_bins)
        for distance, species, _ in selected:
            coordinate = min(radial_bins - 1.000001, (distance / scale - 1.0) * 2.0)
            coordinate = max(0.0, coordinate)
            left = int(coordinate)
            fraction = coordinate - left
            offset = species_index[species] * radial_bins
            radial[offset + left] += 1.0 - fraction
            if left + 1 < radial_bins:
                radial[offset + left + 1] += fraction
        angular = [0.0] * angular_bins
        for first in range(len(selected)):
            for second in range(first + 1, len(selected)):
                va, vb = selected[first][2], selected[second][2]
                cosine = max(-1.0, min(1.0, dot(va, vb) /
                                       (selected[first][0] * selected[second][0])))
                coordinate = (cosine + 1.0) * 0.5 * (angular_bins - 1)
                left = int(coordinate)
                fraction = coordinate - left
                angular[left] += 1.0 - fraction
                if left + 1 < angular_bins:
                    angular[left + 1] += fraction
        descriptors.append(tuple(center_one_hot + radial + angular))
    return tuple(descriptors)


def squared_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def learn_catalog(
    descriptors: Sequence[Sequence[float]],
    tolerance: float = 1e-7,
) -> Tuple[Tuple[Tuple[float, ...], ...], Tuple[int, ...], float]:
    """Greedy tolerance cover: an interpretable prototype per motif type."""
    prototypes: List[Tuple[float, ...]] = []
    labels: List[int] = []
    residual = 0.0
    threshold = tolerance * tolerance
    for descriptor in descriptors:
        distances = [squared_distance(descriptor, prototype)
                     for prototype in prototypes]
        if distances and min(distances) <= threshold:
            label = min(range(len(distances)), key=distances.__getitem__)
            residual += distances[label]
        else:
            label = len(prototypes)
            prototypes.append(tuple(descriptor))
        labels.append(label)
    return tuple(prototypes), tuple(labels), residual


def classify(
    descriptors: Sequence[Sequence[float]],
    prototypes: Sequence[Sequence[float]],
) -> Tuple[int, ...]:
    return tuple(min(range(len(prototypes)),
                     key=lambda index: squared_distance(descriptor,
                                                        prototypes[index]))
                 for descriptor in descriptors)


def rotate(configuration: AtomicConfiguration) -> AtomicConfiguration:
    # A fixed proper rotation: (x,y,z) -> (-y,x,z).
    positions = tuple((-y, x, z) for x, y, z in configuration.positions)
    cell = (tuple(-value for value in configuration.cell[1]),
            configuration.cell[0], configuration.cell[2]) if configuration.cell else None
    return AtomicConfiguration(configuration.name + "-rotated", positions,
                               configuration.species, cell, configuration.periodic,
                               configuration.provenance)


def perturb(configuration: AtomicConfiguration, sigma: float, seed: int) -> AtomicConfiguration:
    rng = random.Random(seed)
    positions = tuple(tuple(value + rng.gauss(0.0, sigma) for value in point)
                      for point in configuration.positions)
    return AtomicConfiguration(configuration.name + "-perturbed", positions,
                               configuration.species, configuration.cell,
                               configuration.periodic, configuration.provenance)


def supercell(
    name: str,
    basis: Sequence[Tuple[Vector, str]],
    repeats: Tuple[int, int, int],
    lattice: Vector,
    provenance: str,
) -> AtomicConfiguration:
    positions: List[Vector] = []
    species: List[str] = []
    for cell_index in itertools.product(*(range(value) for value in repeats)):
        for fractional, chemical in basis:
            positions.append(tuple((cell_index[axis] + fractional[axis]) *
                                   lattice[axis] for axis in range(3)))
            species.append(chemical)
    lengths = tuple(repeats[axis] * lattice[axis] for axis in range(3))
    cell: Matrix = ((lengths[0], 0.0, 0.0),
                    (0.0, lengths[1], 0.0),
                    (0.0, 0.0, lengths[2]))
    return AtomicConfiguration(name, tuple(positions), tuple(species), cell, True,
                               provenance)


def cd6yb_approximant() -> AtomicConfiguration:
    """Experimental Cd6Yb 1/1 Tsai-type approximant (COD 1525048).

    The ten reported asymmetric-unit sites are expanded with space group I 2 3
    (No. 197).  This is deliberately kept as data plus symmetry operations,
    rather than replaced by an idealized cluster.
    """
    asymmetric = (
        ("Cd", (0.0, .2305, .0914)), ("Cd", (.43, .43, .43)),
        ("Cd", (.201, .114, .3434)), ("Cd", (.1645, .1645, .1645)),
        ("Yb", (0.0, .1879, .3014)), ("Cd", (0.0, .4055, .3488)),
        ("Cd", (.4065, 0.0, 0.0)), ("Cd", (.8355, .8355, .8355)),
        ("Cd", (.799, .886, .6566)), ("Cd", (.6956, 0.0, .5)),
    )
    operations = (
        ((0, 1), (1, 1), (2, 1)), ((0, -1), (1, -1), (2, 1)),
        ((0, 1), (1, -1), (2, -1)), ((0, -1), (1, 1), (2, -1)),
        ((2, 1), (0, 1), (1, 1)), ((2, -1), (0, -1), (1, 1)),
        ((2, 1), (0, -1), (1, -1)), ((2, -1), (0, 1), (1, -1)),
        ((1, 1), (2, 1), (0, 1)), ((1, 1), (2, -1), (0, -1)),
        ((1, -1), (2, 1), (0, -1)), ((1, -1), (2, -1), (0, 1)),
    )
    sites: Dict[Tuple[str, int, int, int], Vector] = {}
    for chemical, fractional in asymmetric:
        for operation in operations:
            transformed = tuple((fractional[axis] * sign) % 1.0
                                for axis, sign in operation)
            for centering in (0.0, .5):
                point = tuple((value + centering) % 1.0 for value in transformed)
                key = (chemical,) + tuple(round(value * 10**7) for value in point)
                sites[key] = point  # type: ignore[assignment]
    lattice = 15.638
    ordered = sorted(sites.items())
    positions = tuple(tuple(value * lattice for value in point)
                      for _, point in ordered)
    species = tuple(key[0] for key, _ in ordered)
    cell: Matrix = ((lattice, 0.0, 0.0), (0.0, lattice, 0.0),
                    (0.0, 0.0, lattice))
    return AtomicConfiguration(
        "Cd6Yb-1/1-approximant", positions, species, cell, True,
        "Experimental Palenzona structure, COD 1525048 "
        "(public-domain CIF; I 2 3, a=15.638 Å).")


def benchmark_systems() -> Tuple[AtomicConfiguration, ...]:
    """Real crystallographic prototypes, represented as ideal supercells."""
    b2 = supercell(
        "NiAl-B2", [((0, 0, 0), "Ni"), ((0.5, 0.5, 0.5), "Al")],
        (4, 4, 4), (2.887, 2.887, 2.887),
        "B2 NiAl prototype; lattice parameter is a representative ideal value.")
    l12 = supercell(
        "Cu3Au-L12",
        [((0, 0, 0), "Au"), ((0, .5, .5), "Cu"),
         ((.5, 0, .5), "Cu"), ((.5, .5, 0), "Cu")],
        (4, 4, 4), (3.75, 3.75, 3.75),
        "Cu3Au L1_2 prototype; Materials Project mp-2258 / DOI 10.17188/1198800.")
    zincblende_basis = []
    fcc = ((0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0))
    for point in fcc:
        zincblende_basis.append((point, "Ga"))
        zincblende_basis.append((tuple((value + .25) % 1 for value in point), "As"))
    zincblende = supercell(
        "GaAs-zincblende", zincblende_basis, (3, 3, 3), (5.653, 5.653, 5.653),
        "GaAs zinc-blende crystallographic prototype.")
    rocksalt_basis = []
    for point in fcc:
        rocksalt_basis.append((point, "Na"))
        rocksalt_basis.append((((point[0] + .5) % 1, point[1], point[2]), "Cl"))
    rocksalt = supercell(
        "NaCl-rocksalt", rocksalt_basis, (3, 3, 3), (5.640, 5.640, 5.640),
        "NaCl B1/rock-salt crystallographic prototype.")
    perovskite = supercell(
        "SrTiO3-perovskite",
        [((0, 0, 0), "Sr"), ((.5, .5, .5), "Ti"),
         ((.5, .5, 0), "O"), ((.5, 0, .5), "O"), ((0, .5, .5), "O")],
        (4, 4, 4), (3.905268, 3.905268, 3.905268),
        "Cubic Pm-3m SrTiO3; Materials Project mp-5229, DOI "
        "10.17188/1263154; room-temperature lattice parameter from "
        "DOI 10.1107/S0108768111046738.")
    return b2, l12, zincblende, rocksalt, perovskite, cd6yb_approximant()


def iid_alloy_control(seed: int = 71) -> AtomicConfiguration:
    """Balanced random substitutional alloy on the B2 point geometry."""
    geometry = benchmark_systems()[0]
    rng = random.Random(seed)
    species = ["Ni"] * (len(geometry.positions) // 2)
    species += ["Al"] * (len(geometry.positions) - len(species))
    rng.shuffle(species)
    return AtomicConfiguration(
        "IID-NiAl-null", geometry.positions, tuple(species), geometry.cell, True,
        "Synthetic balanced IID substitutional-alloy null control.")


def evaluate(configuration: AtomicConfiguration, neighbor_count: int = 12) -> AtlasResult:
    clean = local_descriptors(configuration, neighbor_count)
    prototypes, labels, residual = learn_catalog(clean)
    rotated_labels = classify(local_descriptors(rotate(configuration), neighbor_count),
                              prototypes)
    nearest = min(norm(displacement(configuration, 0, j))
                  for j in range(1, len(configuration.positions)))
    noisy = perturb(configuration, sigma=nearest * 0.005, seed=19)
    noisy_labels = classify(local_descriptors(noisy, neighbor_count), prototypes)
    fixed_clean = local_descriptors(configuration, neighbor_count, close_shell=False)
    fixed_prototypes, fixed_labels, _ = learn_catalog(fixed_clean)
    fixed_noisy_labels = classify(
        local_descriptors(noisy, neighbor_count, close_shell=False),
        fixed_prototypes)
    return AtlasResult(
        configuration.name,
        len(configuration.positions),
        len(set(configuration.species)),
        len(prototypes),
        len(configuration.positions) / len(prototypes),
        math.sqrt(residual / max(1, len(configuration.positions))),
        sum(a == b for a, b in zip(labels, noisy_labels)) / len(labels),
        sum(a == b for a, b in zip(labels, rotated_labels)) / len(labels),
        len(fixed_prototypes),
        sum(a == b for a, b in zip(fixed_labels, fixed_noisy_labels)) / len(labels),
    )


def run_suite() -> Tuple[AtlasResult, ...]:
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
