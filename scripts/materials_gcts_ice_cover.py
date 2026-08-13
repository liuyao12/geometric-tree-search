#!/usr/bin/env python3
"""Headless molecular-cover benchmark for proton-ordered ice fixtures.

The learner receives only element-labelled Cartesian positions and a periodic
cell.  It first discovers covalent H2O motifs, then adds overlapping water-
dimer bridges and oxygen-ring void boundaries.  The latter two are connection
clusters: they are what lets a covering search move between otherwise
atom-disjoint water molecules.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from dataclasses import asdict, dataclass
from itertools import product
from typing import Iterable, Sequence

Vector = tuple[float, float, float]


@dataclass(frozen=True)
class IceConfiguration:
    name: str
    positions: tuple[Vector, ...]
    species: tuple[str, ...]
    cell: tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class ClusterOccurrence:
    kind: str
    members: tuple[int, ...]


@dataclass(frozen=True)
class IceCoverResult:
    system: str
    atoms: int
    water_molecules: int
    water_isometry_classes: int
    bridge_occurrences: int
    bridge_isometry_classes: int
    ring_gap_occurrences: int
    ring_gap_isometry_classes: int
    covered_atoms: int
    residual_atom_clusters: int
    search_placements: int
    search_backtracks: int
    reconstructed_atoms: int
    reconstruction_recall: float
    water_only_search_recall: float
    connection_clusters_required: bool
    physical_potential_used: bool


def _add(first: Vector, second: Vector) -> Vector:
    return tuple(a + b for a, b in zip(first, second))  # type: ignore[return-value]


def _sub(first: Vector, second: Vector) -> Vector:
    return tuple(a - b for a, b in zip(first, second))  # type: ignore[return-value]


def _scale(vector: Vector, amount: float) -> Vector:
    return tuple(amount * value for value in vector)  # type: ignore[return-value]


def _norm(vector: Vector) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _matvec(frac: Vector, cell: Sequence[Vector]) -> Vector:
    return tuple(sum(frac[index] * cell[index][axis] for index in range(3))
                 for axis in range(3))  # type: ignore[return-value]


def _inverse3(matrix: Sequence[Vector]) -> tuple[Vector, Vector, Vector]:
    # Cell vectors are rows; this returns the inverse of their transpose so
    # fractional = inverse @ Cartesian.
    a, b, c = matrix
    det = (a[0] * (b[1] * c[2] - b[2] * c[1])
           - b[0] * (a[1] * c[2] - a[2] * c[1])
           + c[0] * (a[1] * b[2] - a[2] * b[1]))
    return (
        ((b[1] * c[2] - b[2] * c[1]) / det,
         (b[2] * c[0] - b[0] * c[2]) / det,
         (b[0] * c[1] - b[1] * c[0]) / det),
        ((c[1] * a[2] - c[2] * a[1]) / det,
         (c[2] * a[0] - c[0] * a[2]) / det,
         (c[0] * a[1] - c[1] * a[0]) / det),
        ((a[1] * b[2] - a[2] * b[1]) / det,
         (a[2] * b[0] - a[0] * b[2]) / det,
         (a[0] * b[1] - a[1] * b[0]) / det),
    )


def _minimum_image(first: Vector, second: Vector,
                   cell: Sequence[Vector]) -> Vector:
    inverse = _inverse3(cell)
    delta = _sub(second, first)
    frac = tuple(sum(inverse[axis][coordinate] * delta[coordinate]
                     for coordinate in range(3)) for axis in range(3))
    wrapped = tuple(value - round(value) for value in frac)
    return _matvec(wrapped, cell)  # type: ignore[arg-type]


def _build_ice(name: str, primitive_cell: Sequence[Vector],
               oxygen_basis: Sequence[Vector], repeats: tuple[int, int, int]) -> IceConfiguration:
    cell = tuple(_scale(primitive_cell[axis], repeats[axis])
                 for axis in range(3))
    oxygen_positions: list[Vector] = []
    oxygen_cells: list[tuple[int, int, int, int]] = []
    for i, j, k in product(*(range(value) for value in repeats)):
        for basis_index, basis in enumerate(oxygen_basis):
            frac = ((i + basis[0]) / repeats[0],
                    (j + basis[1]) / repeats[1],
                    (k + basis[2]) / repeats[2])
            oxygen_positions.append(_matvec(frac, cell))
            oxygen_cells.append((i, j, k, basis_index))

    # Learn the tetrahedral O network directly from geometry, then place two
    # covalent protons along two deterministic network edges per oxygen.
    neighbors: list[list[tuple[float, int, Vector]]] = []
    for index, point in enumerate(oxygen_positions):
        distances = []
        for other, candidate in enumerate(oxygen_positions):
            if other == index:
                continue
            vector = _minimum_image(point, candidate, cell)
            distances.append((_norm(vector), other, vector))
        distances.sort(key=lambda item: (item[0], item[1]))
        neighbors.append(distances[:4])

    positions = list(oxygen_positions)
    species = ["O"] * len(oxygen_positions)
    bond = .9572
    for index, point in enumerate(oxygen_positions):
        i, j, k, basis_index = oxygen_cells[index]
        order = sorted(neighbors[index], key=lambda item: (
            round(item[2][2], 6), round(item[2][1], 6), round(item[2][0], 6)))
        offset = (i + 2 * j + k + basis_index) % 4
        chosen = (order[offset], order[(offset + 1) % 4])
        for distance, _, vector in chosen:
            positions.append(_add(point, _scale(vector, bond / distance)))
            species.append("H")
    return IceConfiguration(name, tuple(positions), tuple(species), cell)  # type: ignore[arg-type]


def ice_ic(repeats: tuple[int, int, int] = (2, 2, 2)) -> IceConfiguration:
    a = 6.36
    cell = ((a, 0.0, 0.0), (0.0, a, 0.0), (0.0, 0.0, a))
    basis = ((0.0, 0.0, 0.0), (0.0, .5, .5), (.5, 0.0, .5),
             (.5, .5, 0.0), (.25, .25, .25), (.25, .75, .75),
             (.75, .25, .75), (.75, .75, .25))
    return _build_ice("ice-Ic", cell, basis, repeats)


def ice_ih(repeats: tuple[int, int, int] = (3, 3, 2)) -> IceConfiguration:
    a, c, u = 4.518, 7.357, 3 / 8
    cell = ((a, 0.0, 0.0), (-a / 2, math.sqrt(3) * a / 2, 0.0),
            (0.0, 0.0, c))
    # Wurtzite/ice-Ih oxygen network: two interpenetrating hexagonal
    # sublattices with four nearly equal O--O neighbors.
    basis = ((0.0, 0.0, 0.0), (2 / 3, 1 / 3, .5),
             (0.0, 0.0, u), (2 / 3, 1 / 3, .5 + u))
    return _build_ice("ice-Ih", cell, basis, repeats)


def _signature(configuration: IceConfiguration, members: Iterable[int]) -> tuple:
    indices = tuple(sorted(members))
    pairs = []
    for right, second in enumerate(indices):
        for first in indices[:right]:
            pair = tuple(sorted((configuration.species[first],
                                 configuration.species[second])))
            distance = _norm(_minimum_image(configuration.positions[first],
                                            configuration.positions[second],
                                            configuration.cell))
            pairs.append((pair, round(distance, 2)))
    return (tuple(sorted(configuration.species[index] for index in indices)),
            tuple(sorted(pairs)))


def discover_cover(configuration: IceConfiguration) -> tuple[
        tuple[ClusterOccurrence, ...], tuple[ClusterOccurrence, ...],
        tuple[ClusterOccurrence, ...]]:
    oxygen = [index for index, species in enumerate(configuration.species)
              if species == "O"]
    hydrogen = [index for index, species in enumerate(configuration.species)
                if species == "H"]
    waters = []
    owner: dict[int, int] = {}
    for oxygen_index in oxygen:
        near = sorted((
            _norm(_minimum_image(configuration.positions[oxygen_index],
                                configuration.positions[h], configuration.cell)), h)
                      for h in hydrogen)
        bonded = tuple(index for distance, index in near if distance < 1.16)[:2]
        if len(bonded) != 2:
            raise AssertionError("oxygen did not resolve to one H2O motif")
        water_index = len(waters)
        waters.append(ClusterOccurrence("H2O", (oxygen_index, *bonded)))
        for atom in (oxygen_index, *bonded):
            owner[atom] = water_index

    bridges = set()
    oxygen_set = set(oxygen)
    for water_index, water in enumerate(waters):
        donor_oxygen, *protons = water.members
        for proton in protons:
            candidates = sorted((
                _norm(_minimum_image(configuration.positions[proton],
                                    configuration.positions[acceptor], configuration.cell)),
                acceptor) for acceptor in oxygen_set if acceptor != donor_oxygen)
            distance, acceptor = candidates[0]
            if distance < 2.25:
                acceptor_water = owner[acceptor]
                pair = tuple(sorted((water_index, acceptor_water)))
                if pair[0] != pair[1]:
                    bridges.add(pair)
    bridge_occurrences = tuple(ClusterOccurrence(
        "H2O···H2O bridge", tuple(sorted(set(waters[first].members)
                                         | set(waters[second].members))))
                               for first, second in sorted(bridges))

    adjacency = {index: set() for index in range(len(waters))}
    for first, second in bridges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    rings: set[tuple[int, ...]] = set()
    for start in adjacency:
        stack = [(start, (start,))]
        while stack:
            current, path = stack.pop()
            if len(path) == 6:
                if start in adjacency[current]:
                    rotations = [path[index:] + path[:index]
                                 for index in range(6)]
                    reverse = tuple(reversed(path))
                    rotations += [reverse[index:] + reverse[:index]
                                  for index in range(6)]
                    rings.add(min(rotations))
                continue
            for neighbor in adjacency[current]:
                if neighbor <= start or neighbor in path:
                    continue
                stack.append((neighbor, path + (neighbor,)))
    gap_occurrences = tuple(ClusterOccurrence(
        "oxygen-ring void boundary",
        tuple(sorted(set().union(*(set(waters[index].members)
                                  for index in ring)))))
                            for ring in sorted(rings))
    return tuple(waters), bridge_occurrences, gap_occurrences


def _reconstruct(atom_count: int, waters: Sequence[ClusterOccurrence],
                 connections: Sequence[ClusterOccurrence]) -> tuple[int, int, int]:
    selected = [waters[0]]
    covered = set(waters[0].members)
    candidates = list(connections) + list(waters[1:])
    backtracks = 0
    while candidates:
        legal = [(len(covered.intersection(candidate.members)),
                  len(set(candidate.members) - covered), index, candidate)
                 for index, candidate in enumerate(candidates)]
        legal = [entry for entry in legal if entry[0] >= 2 and entry[1] > 0]
        if not legal:
            break
        _, _, index, candidate = max(legal, key=lambda entry: (
            entry[0], entry[1], -entry[2]))
        selected.append(candidate)
        covered.update(candidate.members)
        candidates.pop(index)
    return len(covered), len(selected), backtracks


def evaluate(configuration: IceConfiguration) -> IceCoverResult:
    waters, bridges, gaps = discover_cover(configuration)
    water_signatures = {_signature(configuration, item.members)
                        for item in waters}
    bridge_signatures = {_signature(configuration, item.members)
                         for item in bridges}
    gap_signatures = {_signature(configuration, item.members)
                      for item in gaps}
    covered = set().union(*(set(item.members) for item in waters))
    water_only, _, _ = _reconstruct(len(configuration.positions), waters, ())
    reconstructed, placements, backtracks = _reconstruct(
        len(configuration.positions), waters, (*bridges, *gaps))
    return IceCoverResult(
        configuration.name, len(configuration.positions), len(waters),
        len(water_signatures), len(bridges), len(bridge_signatures), len(gaps),
        len(gap_signatures), len(covered), len(configuration.positions) - len(covered),
        placements, backtracks, reconstructed,
        reconstructed / len(configuration.positions),
        water_only / len(configuration.positions),
        reconstructed > water_only, False)


def evaluate_all() -> tuple[IceCoverResult, IceCoverResult]:
    return evaluate(ice_ih()), evaluate(ice_ic())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = evaluate_all()
    print(json.dumps([asdict(result) for result in results], indent=2)
          if args.json else results)


if __name__ == "__main__":
    main()
