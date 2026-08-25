#!/usr/bin/env python3
"""Generic connected-motif, connection, and void-boundary discovery.

The learner accepts only element labels, Cartesian positions, and an optional
periodic cell.  It does not receive a material/family name, molecular formula,
space group, lattice type, expected coordination, or expected ring size.

There are three deliberately separate layers:

1. A valence-bounded covalent graph is inferred from standard element radii.
   Its finite connected components are the primitive molecular occurrences.
2. A nearest-shell graph between those components supplies overlapping
   two-component connection clusters.
3. Chordless cycles of the connection graph become explicit void-boundary
   clusters.  They cover the interstitial topology rather than pretending that
   every gap is centred on an atom.

This is a generic molecular-crystal front end for GCTS.  Extended covalent
networks are rejected explicitly and should fall back to the irregular
point-set support learner instead of being broken into fictitious molecules.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Optional, Sequence

Vector = tuple[float, float, float]
Cell = tuple[Vector, Vector, Vector]


# Single-bond covalent radii (angstrom) and conservative ordinary valence
# bounds.  The table is chemistry metadata, not a water-specific rule.  A
# caller may extend/replace it for unusual oxidation or coordination states.
DEFAULT_COVALENT_RADII: Mapping[str, float] = {
    "H": .31, "D": .31, "B": .84, "C": .76, "N": .71, "O": .66, "F": .57,
    "Si": 1.11, "P": 1.07, "S": 1.05, "Cl": 1.02,
    "Ge": 1.20, "As": 1.19, "Se": 1.20, "Br": 1.20,
    "I": 1.39,
}
DEFAULT_VALENCE_BOUNDS: Mapping[str, int] = {
    "H": 1, "D": 1, "B": 3, "C": 4, "N": 3, "O": 2, "F": 1,
    "Si": 4, "P": 5, "S": 6, "Cl": 1,
    "Ge": 4, "As": 5, "Se": 6, "Br": 1, "I": 1,
}


@dataclass(frozen=True)
class MolecularOccurrence:
    occurrence_id: int
    type_id: int
    members: tuple[int, ...]
    formula: tuple[tuple[str, int], ...]
    signature: tuple


@dataclass(frozen=True)
class ConnectionOccurrence:
    occurrence_id: int
    type_id: int
    components: tuple[int, int]
    members: tuple[int, ...]
    signature: tuple


@dataclass(frozen=True)
class VoidBoundaryOccurrence:
    occurrence_id: int
    type_id: int
    components: tuple[int, ...]
    boundary_members: tuple[int, ...]
    signature: tuple


@dataclass(frozen=True)
class MolecularGapCover:
    atoms: int
    covalent_edges: tuple[tuple[int, int], ...]
    molecules: tuple[MolecularOccurrence, ...]
    connections: tuple[ConnectionOccurrence, ...]
    void_boundaries: tuple[VoidBoundaryOccurrence, ...]
    molecule_type_count: int
    connection_type_count: int
    void_type_count: int
    covered_atoms: int
    residual_atoms: tuple[int, ...]
    component_graph_connected: bool
    extended_network_rejected: bool
    material_label_used: bool = False
    expected_formula_used: bool = False
    expected_ring_size_used: bool = False


def _sub(left: Vector, right: Vector) -> Vector:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _scale(vector: Vector, factor: float) -> Vector:
    return tuple(factor * value for value in vector)  # type: ignore[return-value]


def _norm(vector: Vector) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _matvec(frac: Vector, cell: Sequence[Vector]) -> Vector:
    return tuple(sum(frac[index] * cell[index][axis] for index in range(3))
                 for axis in range(3))  # type: ignore[return-value]


def _inverse3(matrix: Sequence[Vector]) -> Cell:
    a, b, c = matrix
    determinant = (a[0] * (b[1] * c[2] - b[2] * c[1])
                   - b[0] * (a[1] * c[2] - a[2] * c[1])
                   + c[0] * (a[1] * b[2] - a[2] * b[1]))
    if abs(determinant) <= 1e-12:
        raise ValueError("periodic cell must be nonsingular")
    return (
        ((b[1] * c[2] - b[2] * c[1]) / determinant,
         (b[2] * c[0] - b[0] * c[2]) / determinant,
         (b[0] * c[1] - b[1] * c[0]) / determinant),
        ((c[1] * a[2] - c[2] * a[1]) / determinant,
         (c[2] * a[0] - c[0] * a[2]) / determinant,
         (c[0] * a[1] - c[1] * a[0]) / determinant),
        ((a[1] * b[2] - a[2] * b[1]) / determinant,
         (a[2] * b[0] - a[0] * b[2]) / determinant,
         (a[0] * b[1] - a[1] * b[0]) / determinant),
    )


def _displacement(first: Vector, second: Vector,
                  cell: Optional[Sequence[Vector]], inverse: Optional[Cell]) -> Vector:
    delta = _sub(second, first)
    if cell is None:
        return delta
    assert inverse is not None
    fractional = tuple(sum(inverse[axis][coordinate] * delta[coordinate]
                           for coordinate in range(3)) for axis in range(3))
    wrapped = tuple(value - round(value) for value in fractional)
    return _matvec(wrapped, cell)  # type: ignore[arg-type]


def _distance(first: Vector, second: Vector,
              cell: Optional[Sequence[Vector]], inverse: Optional[Cell]) -> float:
    return _norm(_displacement(first, second, cell, inverse))


def _formula(species: Sequence[str], members: Iterable[int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(species[index] for index in members).items()))


def _colored_metric_signature(species: Sequence[str], positions: Sequence[Vector],
                              members: Sequence[int], cell: Optional[Sequence[Vector]],
                              inverse: Optional[Cell], tolerance: float) -> tuple:
    pairs = []
    for offset, second in enumerate(members):
        for first in members[:offset]:
            chemistry = tuple(sorted((species[first], species[second])))
            distance = _distance(positions[first], positions[second], cell, inverse)
            pairs.append((chemistry, int(round(distance / tolerance))))
    return _formula(species, members), tuple(sorted(pairs))


def unwrapped_cluster_sites(
    species: Sequence[str], positions: Sequence[Sequence[float]],
    members: Sequence[int], *, cell: Optional[Sequence[Sequence[float]]] = None,
) -> tuple[tuple[str, Vector], ...]:
    """Return one finite cluster in a continuous Cartesian image.

    This is the geometry passed to the proper-SE(3) port compiler.  The first
    member is only a temporary unwrapping anchor; centring and canonical pose
    fitting remain centre-free downstream.
    """
    if not members:
        raise ValueError("a cluster needs at least one member")
    points = tuple(tuple(float(value) for value in point) for point in positions)
    periodic_cell = None if cell is None else tuple(tuple(float(value) for value in row) for row in cell)
    inverse = None if periodic_cell is None else _inverse3(periodic_cell)
    anchor = points[members[0]]
    result = []
    for index in members:
        point = anchor if index == members[0] else _add(
            anchor, _displacement(anchor, points[index], periodic_cell, inverse))
        result.append((species[index], point))
    return tuple(result)


def _components(atom_count: int, edges: Iterable[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    adjacency = [set() for _ in range(atom_count)]
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    remaining = set(range(atom_count))
    result = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack.extend(adjacency[current] - component)
        remaining -= component
        result.append(tuple(sorted(component)))
    return tuple(result)


def _infer_covalent_edges(species: Sequence[str], positions: Sequence[Vector],
                          cell: Optional[Sequence[Vector]], inverse: Optional[Cell],
                          radii: Mapping[str, float], valences: Mapping[str, int],
                          bond_factor: float) -> tuple[tuple[int, int], ...]:
    missing = sorted(set(species) - set(radii))
    if missing:
        raise ValueError(f"missing covalent radii for: {', '.join(missing)}")
    missing_valence = sorted(set(species) - set(valences))
    if missing_valence:
        raise ValueError(f"missing valence bounds for: {', '.join(missing_valence)}")
    candidates = []
    for first, second in combinations(range(len(positions)), 2):
        distance = _distance(positions[first], positions[second], cell, inverse)
        reference = radii[species[first]] + radii[species[second]]
        normalized = distance / reference
        if normalized <= bond_factor:
            candidates.append((normalized, distance, first, second))
    candidates.sort()
    degree = [0] * len(positions)
    edges = []
    for _, _, first, second in candidates:
        if degree[first] >= valences[species[first]] or degree[second] >= valences[species[second]]:
            continue
        edges.append((first, second))
        degree[first] += 1
        degree[second] += 1
    return tuple(sorted(edges))


def _component_anchor(component: Sequence[int], species: Sequence[str],
                      positions: Sequence[Vector], cell: Optional[Sequence[Vector]],
                      inverse: Optional[Cell], tolerance: float) -> Vector:
    anchor = positions[component[0]]
    unwrapped = [anchor]
    unwrapped.extend(_add(anchor, _displacement(anchor, positions[index], cell, inverse))
                     for index in component[1:])
    populations = Counter(species[index] for index in component)
    keys = []
    for local, atom_index in enumerate(component):
        radial = tuple(sorted((species[other], int(round(_distance(
            positions[atom_index], positions[other], cell, inverse) / tolerance)))
                              for other in component if other != atom_index))
        keys.append((populations[species[atom_index]], species[atom_index], radial))
    minimum = min(keys)
    winners = [index for index, key in enumerate(keys) if key == minimum]
    if len(winners) == 1:
        return unwrapped[winners[0]]
    return _scale(tuple(sum(point[axis] for point in unwrapped) for axis in range(3)),
                  1 / len(unwrapped))  # type: ignore[arg-type]


def _nearest_shell_graph(anchors: Sequence[Vector], cell: Optional[Sequence[Vector]],
                         inverse: Optional[Cell], shell_factor: float) -> tuple[tuple[int, int], ...]:
    if len(anchors) < 2:
        return ()
    neighborhoods = []
    for first in range(len(anchors)):
        ranked = sorted((_distance(anchors[first], anchors[second], cell, inverse), second)
                        for second in range(len(anchors)) if second != first)
        nearest = ranked[0][0]
        neighborhoods.append({second for distance, second in ranked
                              if distance <= nearest * shell_factor + 1e-9})
    # The union is robust to mildly off-centre molecular centroids.  Spurious
    # long links are still excluded by each endpoint's first-shell cutoff.
    return tuple((first, second) for first in range(len(anchors))
                 for second in range(first + 1, len(anchors))
                 if second in neighborhoods[first] or first in neighborhoods[second])


def _canonical_cycle(path: Sequence[int]) -> tuple[int, ...]:
    sequence = tuple(path)
    reverse = tuple(reversed(sequence))
    rotations = [sequence[index:] + sequence[:index] for index in range(len(sequence))]
    rotations += [reverse[index:] + reverse[:index] for index in range(len(sequence))]
    return min(rotations)


def _chordless_cycles(vertex_count: int, edges: Sequence[tuple[int, int]],
                      maximum_size: int) -> tuple[tuple[int, ...], ...]:
    adjacency = [set() for _ in range(vertex_count)]
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    cycles = set()
    for start in range(vertex_count):
        stack = [(start, (start,))]
        while stack:
            current, path = stack.pop()
            for neighbor in sorted(adjacency[current], reverse=True):
                if neighbor == start and len(path) >= 3:
                    cycle = _canonical_cycle(path)
                    edge_count = sum(1 for a, b in combinations(cycle, 2)
                                     if b in adjacency[a])
                    if edge_count == len(cycle):
                        cycles.add(cycle)
                    continue
                if len(path) >= maximum_size or neighbor <= start or neighbor in path:
                    continue
                stack.append((neighbor, path + (neighbor,)))
    # A chordless graph can still contain large peripheral cycles that are
    # unions of smaller physical rings.  Keep the locally shortest cycle at
    # every boundary edge.  This is a graph-derived face criterion; no ring
    # size is prescribed.
    minimum_by_edge: dict[tuple[int, int], int] = {}
    for cycle in cycles:
        for index, first in enumerate(cycle):
            second = cycle[(index + 1) % len(cycle)]
            edge = tuple(sorted((first, second)))
            minimum_by_edge[edge] = min(minimum_by_edge.get(edge, len(cycle)), len(cycle))
    local_faces = [cycle for cycle in cycles if all(
        minimum_by_edge[tuple(sorted((first, cycle[(index + 1) % len(cycle)])))] == len(cycle)
        for index, first in enumerate(cycle))]
    return tuple(sorted(local_faces, key=lambda cycle: (len(cycle), cycle)))


def _connected(vertex_count: int, edges: Sequence[tuple[int, int]]) -> bool:
    if vertex_count <= 1:
        return True
    adjacency = [set() for _ in range(vertex_count)]
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    seen = {0}
    stack = [0]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current] - seen:
            seen.add(neighbor)
            stack.append(neighbor)
    return len(seen) == vertex_count


def learn_molecular_gap_cover(
    species: Sequence[str],
    positions: Sequence[Sequence[float]],
    *,
    cell: Optional[Sequence[Sequence[float]]] = None,
    covalent_radii: Mapping[str, float] = DEFAULT_COVALENT_RADII,
    valence_bounds: Mapping[str, int] = DEFAULT_VALENCE_BOUNDS,
    bond_factor: float = 1.25,
    contact_shell_factor: float = 1.16,
    descriptor_tolerance: float = .03,
    maximum_void_cycle: int = 8,
    maximum_molecule_fraction: float = .25,
) -> MolecularGapCover:
    """Learn molecular, connection, and void-boundary cluster classes."""
    if len(species) != len(positions) or not positions:
        raise ValueError("species and nonempty positions must have equal length")
    points = tuple(tuple(float(value) for value in point) for point in positions)
    if any(len(point) != 3 or not all(math.isfinite(value) for value in point) for point in points):
        raise ValueError("positions must be finite Cartesian triples")
    periodic_cell = None if cell is None else tuple(tuple(float(value) for value in row) for row in cell)
    if periodic_cell is not None and (len(periodic_cell) != 3 or any(len(row) != 3 for row in periodic_cell)):
        raise ValueError("cell must contain three Cartesian vectors")
    inverse = None if periodic_cell is None else _inverse3(periodic_cell)
    if not (1 < bond_factor < 2) or not (1 < contact_shell_factor < 2):
        raise ValueError("bond and contact factors must lie between one and two")
    if descriptor_tolerance <= 0 or maximum_void_cycle < 3:
        raise ValueError("invalid descriptor tolerance or maximum cycle")

    edges = _infer_covalent_edges(species, points, periodic_cell, inverse,
                                  covalent_radii, valence_bounds, bond_factor)
    components = _components(len(points), edges)
    extended = max(map(len, components)) > len(points) * maximum_molecule_fraction
    if extended:
        return MolecularGapCover(len(points), edges, (), (), (), 0, 0, 0, 0,
                                 tuple(range(len(points))), False, True)

    molecule_signatures = [_colored_metric_signature(
        species, points, component, periodic_cell, inverse, descriptor_tolerance)
        for component in components]
    molecule_type_keys = {signature: index for index, signature in
                          enumerate(sorted(set(molecule_signatures)))}
    molecules = tuple(MolecularOccurrence(
        occurrence_id=index,
        type_id=molecule_type_keys[molecule_signatures[index]],
        members=component,
        formula=_formula(species, component),
        signature=molecule_signatures[index],
    ) for index, component in enumerate(components))

    anchors = tuple(_component_anchor(component, species, points, periodic_cell,
                                      inverse, descriptor_tolerance)
                    for component in components)
    component_edges = _nearest_shell_graph(anchors, periodic_cell, inverse,
                                           contact_shell_factor)
    connection_keys = []
    for first, second in component_edges:
        members = tuple(sorted(set(components[first]) | set(components[second])))
        metric = _colored_metric_signature(species, points, members, periodic_cell,
                                           inverse, descriptor_tolerance)
        component_pair = tuple(sorted((molecules[first].type_id, molecules[second].type_id)))
        connection_keys.append((component_pair, metric))
    connection_type_keys = {signature: index for index, signature in
                            enumerate(sorted(set(connection_keys)))}
    connections = tuple(ConnectionOccurrence(
        occurrence_id=index,
        type_id=connection_type_keys[connection_keys[index]],
        components=edge,
        members=tuple(sorted(set(components[edge[0]]) | set(components[edge[1]]))),
        signature=connection_keys[index],
    ) for index, edge in enumerate(component_edges))

    cycles = _chordless_cycles(len(components), component_edges, maximum_void_cycle)
    void_keys = []
    for cycle in cycles:
        edge_lengths = tuple(sorted(int(round(_distance(
            anchors[cycle[index]], anchors[cycle[(index + 1) % len(cycle)]],
            periodic_cell, inverse) / descriptor_tolerance)) for index in range(len(cycle))))
        type_cycle = tuple(molecules[index].type_id for index in cycle)
        void_keys.append((len(cycle), _canonical_cycle(type_cycle), edge_lengths))
    void_type_keys = {signature: index for index, signature in
                      enumerate(sorted(set(void_keys)))}
    voids = tuple(VoidBoundaryOccurrence(
        occurrence_id=index,
        type_id=void_type_keys[void_keys[index]],
        components=cycle,
        boundary_members=tuple(sorted(set().union(*(set(components[item]) for item in cycle)))),
        signature=void_keys[index],
    ) for index, cycle in enumerate(cycles))

    covered = set().union(*(set(component) for component in components))
    return MolecularGapCover(
        atoms=len(points), covalent_edges=edges, molecules=molecules,
        connections=connections, void_boundaries=voids,
        molecule_type_count=len(molecule_type_keys),
        connection_type_count=len(connection_type_keys),
        void_type_count=len(void_type_keys), covered_atoms=len(covered),
        residual_atoms=tuple(sorted(set(range(len(points))) - covered)),
        component_graph_connected=_connected(len(components), component_edges),
        extended_network_rejected=False,
    )
