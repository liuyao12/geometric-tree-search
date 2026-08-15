#!/usr/bin/env python3
"""Deterministic sparse reduction of an irregular-support occurrence graph.

The reducer consumes only an already learned ``IrregularPortProgram``.  Its
nodes are finite support occurrences; its edges are witnessed, train-admitted
oriented port relations.  It never reads a cell, material/family label, target
window, potential, or absolute preferred frame.

Reduction has three explicit phases:

1. a greedy minimum-description overlapping cover (one reference token per
   occurrence; maximize newly covered atoms, with deterministic overlap ties),
2. shortest witnessed connector paths between cover components, adding the
   fewest currently absent occurrences available at each step, and
3. a maximum-overlap spanning forest plus one canonical edge for every
   distinct short-cycle signature.

The cover and connector steps are standard deterministic approximations: exact
minimum set cover and minimum Steiner tree are NP-hard.  Their approximation
status is exposed in the result rather than hidden behind an optimality claim.
"""

from __future__ import annotations

import heapq
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from materials_gcts_irregular_port_atlas import IrregularPortProgram

PortLabel = tuple[int, int, tuple[int, ...]]


@dataclass(frozen=True)
class SparseOccurrenceEdge:
    left: int
    right: int
    overlap_atoms: int
    canonical_port_label: PortLabel


@dataclass(frozen=True)
class SparseOccurrenceGraph:
    source_nodes: int
    source_edges: int
    coverable_atoms: int
    covered_atoms: int
    cover_nodes: tuple[int, ...]
    connector_nodes: tuple[int, ...]
    retained_nodes: tuple[int, ...]
    spanning_edges: tuple[SparseOccurrenceEdge, ...]
    cycle_edges: tuple[SparseOccurrenceEdge, ...]
    retained_edges: tuple[SparseOccurrenceEdge, ...]
    source_components: int
    retained_components: int
    cover_components_before_connectors: int
    node_reduction: float
    edge_reduction: float
    complete_repeated_support_cover: bool
    every_connector_witnessed: bool
    connected_when_source_connected: bool
    set_cover_optimality_claimed: bool
    steiner_optimality_claimed: bool


class _DisjointSet:
    def __init__(self, nodes: Iterable[int]):
        self.parent = {node: node for node in nodes}

    def find(self, node: int) -> int:
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, left: int, right: int) -> bool:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return False
        if left_root > right_root:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        return True


def _source_edges(program: IrregularPortProgram) -> tuple[SparseOccurrenceEdge, ...]:
    admitted = {
        (port.parent_type, port.child_type, port.symmetry_orbit_key)
        for port in program.atlas.ports}
    supports = {occurrence_id: frozenset(members)
                for occurrence_id, members in program.occurrence_supports}
    labels: dict[tuple[int, int], list[PortLabel]] = defaultdict(list)
    for parent, child, parent_type, child_type, pose_key in (
            program.atlas.relation_classes):
        label = parent_type, child_type, pose_key
        if label not in admitted:
            continue
        pair = min(parent, child), max(parent, child)
        labels[pair].append(label)
    result = []
    for (left, right), pair_labels in sorted(labels.items()):
        overlap = len(supports[left].intersection(supports[right]))
        if overlap < program.minimum_shared_atoms:
            continue
        result.append(SparseOccurrenceEdge(
            left, right, overlap, min(pair_labels, key=repr)))
    return tuple(result)


def _components(nodes: Iterable[int], edges: Iterable[SparseOccurrenceEdge]) -> int:
    nodes = tuple(nodes)
    if not nodes:
        return 0
    union = _DisjointSet(nodes)
    allowed = set(nodes)
    for edge in edges:
        if edge.left in allowed and edge.right in allowed:
            union.union(edge.left, edge.right)
    return len({union.find(node) for node in nodes})


def _greedy_cover(
    supports: dict[int, frozenset[int]],
) -> tuple[tuple[int, ...], frozenset[int]]:
    target = frozenset(atom for support in supports.values() for atom in support)
    uncovered = set(target)
    selected: list[int] = []
    selected_atoms: set[int] = set()
    remaining = set(supports)
    while uncovered:
        node = max(remaining, key=lambda candidate: (
            len(supports[candidate].intersection(uncovered)),
            len(supports[candidate].intersection(selected_atoms)),
            len(supports[candidate]), -candidate))
        gain = supports[node].intersection(uncovered)
        if not gain:
            break
        selected.append(node)
        selected_atoms.update(supports[node])
        uncovered.difference_update(gain)
        remaining.remove(node)
    return tuple(selected), target


def _induced_components(
    selected: set[int], adjacency: dict[int, set[int]],
) -> tuple[frozenset[int], ...]:
    remaining = set(selected)
    result = []
    while remaining:
        root = min(remaining)
        component = {root}
        queue = deque((root,))
        remaining.remove(root)
        while queue:
            node = queue.popleft()
            for neighbor in sorted(adjacency.get(node, ())):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(frozenset(component))
    return tuple(sorted(result, key=lambda item: tuple(sorted(item))))


def _shortest_component_path(
    components: tuple[frozenset[int], ...],
    adjacency: dict[int, set[int]],
) -> tuple[int, ...] | None:
    """Find a path minimizing absent connector nodes, then lexicographic path."""
    best = None
    selected = set().union(*components)
    for component_index, source in enumerate(components):
        target_nodes = set().union(*(
            component for index, component in enumerate(components)
            if index != component_index))
        # Multi-source Dijkstra with a zero cost for already selected nodes and
        # unit cost for a new connector. Ordinary BFS minimizes edge count,
        # which is not the same objective when a path can cross selected nodes.
        queue = []
        distances: dict[int, tuple[int, int, tuple[int, ...]]] = {}
        for node in sorted(source):
            state = (0, 0, (node,))
            distances[node] = state
            heapq.heappush(queue, (*state, node))
        path = None
        while queue:
            connector_cost, edge_count, prefix, node = heapq.heappop(queue)
            if distances.get(node) != (connector_cost, edge_count, prefix):
                continue
            if node in target_nodes:
                path = prefix
                break
            for neighbor in sorted(adjacency.get(node, ())):
                candidate = (
                    connector_cost + (neighbor not in selected),
                    edge_count + 1, prefix + (neighbor,))
                if neighbor not in distances or candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    heapq.heappush(queue, (*candidate, neighbor))
        if path is None:
            continue
        candidate = (sum(node not in selected for node in path[1:-1]),
                     len(path), path)
        if best is None or candidate < best:
            best = candidate
    return None if best is None else best[2]


def _tree_path(
    start: int, finish: int,
    adjacency: dict[int, list[tuple[int, SparseOccurrenceEdge]]],
) -> tuple[tuple[int, ...], tuple[SparseOccurrenceEdge, ...]] | None:
    queue = deque((start,))
    predecessor: dict[int, tuple[int, SparseOccurrenceEdge] | None] = {
        start: None}
    while queue:
        node = queue.popleft()
        if node == finish:
            break
        for neighbor, edge in sorted(adjacency.get(node, ()),
                                     key=lambda item: item[0]):
            if neighbor not in predecessor:
                predecessor[neighbor] = node, edge
                queue.append(neighbor)
    if finish not in predecessor:
        return None
    nodes = [finish]
    edges = []
    cursor = finish
    while predecessor[cursor] is not None:
        previous, edge = predecessor[cursor]  # type: ignore[misc]
        nodes.append(previous)
        edges.append(edge)
        cursor = previous
    return tuple(reversed(nodes)), tuple(reversed(edges))


def _cycle_signature(
    nodes: tuple[int, ...], path_edges: tuple[SparseOccurrenceEdge, ...],
    closing: SparseOccurrenceEdge, node_types: dict[int, int],
) -> tuple[str, ...]:
    edge_labels = tuple(repr(edge.canonical_port_label)
                        for edge in path_edges + (closing,))
    node_labels = tuple(str(node_types[node]) for node in nodes)
    sequence = tuple(value for pair in zip(node_labels, edge_labels)
                     for value in pair)
    reversed_sequence = tuple(reversed(sequence))
    rotations = tuple(sequence[offset:] + sequence[:offset]
                      for offset in range(len(sequence)))
    reverse_rotations = tuple(reversed_sequence[offset:] +
                              reversed_sequence[:offset]
                              for offset in range(len(sequence)))
    return min(rotations + reverse_rotations)


def reduce_occurrence_graph(
    program: IrregularPortProgram, *, maximum_cycle_length: int = 4,
) -> SparseOccurrenceGraph:
    """Return a sparse, covering, witnessed occurrence graph."""
    if maximum_cycle_length < 3:
        raise ValueError("maximum_cycle_length must be at least three")
    supports = {occurrence_id: frozenset(members)
                for occurrence_id, members in program.occurrence_supports}
    node_types = {occurrence.occurrence_id: occurrence.type_id
                  for occurrence in program.occurrences}
    edges = _source_edges(program)
    adjacency: dict[int, set[int]] = defaultdict(set)
    edge_by_pair = {}
    for edge in edges:
        adjacency[edge.left].add(edge.right)
        adjacency[edge.right].add(edge.left)
        edge_by_pair[(edge.left, edge.right)] = edge

    cover_nodes, coverable = _greedy_cover(supports)
    selected = set(cover_nodes)
    cover_components = _induced_components(selected, adjacency)
    before = len(cover_components)
    connectors: list[int] = []
    while len(cover_components) > 1:
        path = _shortest_component_path(cover_components, adjacency)
        if path is None:
            break
        for node in path[1:-1]:
            if node not in selected:
                selected.add(node)
                connectors.append(node)
        next_components = _induced_components(selected, adjacency)
        if len(next_components) >= len(cover_components):
            break
        cover_components = next_components

    induced_edges = tuple(edge for edge in edges
                          if edge.left in selected and edge.right in selected)
    union = _DisjointSet(selected)
    spanning = []
    for edge in sorted(induced_edges, key=lambda item: (
            -item.overlap_atoms, repr(item.canonical_port_label),
            item.left, item.right)):
        if union.union(edge.left, edge.right):
            spanning.append(edge)
    tree_adjacency: dict[int, list[tuple[int, SparseOccurrenceEdge]]] = defaultdict(list)
    for edge in spanning:
        tree_adjacency[edge.left].append((edge.right, edge))
        tree_adjacency[edge.right].append((edge.left, edge))
    tree_pairs = {(edge.left, edge.right) for edge in spanning}
    cycle_representatives: dict[tuple[str, ...], SparseOccurrenceEdge] = {}
    for edge in induced_edges:
        if (edge.left, edge.right) in tree_pairs:
            continue
        path = _tree_path(edge.left, edge.right, tree_adjacency)
        if path is None:
            continue
        path_nodes, path_edges = path
        cycle_length = len(path_edges) + 1
        if cycle_length > maximum_cycle_length:
            continue
        signature = _cycle_signature(
            path_nodes, path_edges, edge, node_types)
        prior = cycle_representatives.get(signature)
        if prior is None or (-edge.overlap_atoms, edge.left, edge.right) < (
                -prior.overlap_atoms, prior.left, prior.right):
            cycle_representatives[signature] = edge
    cycle_edges = tuple(sorted(cycle_representatives.values(),
                               key=lambda item: (item.left, item.right)))
    retained_edges = tuple(sorted((*spanning, *cycle_edges),
                                  key=lambda item: (item.left, item.right)))
    retained_nodes = tuple(sorted(selected))
    source_components = _components(supports, edges)
    retained_components = _components(retained_nodes, retained_edges)
    covered = frozenset(atom for node in cover_nodes for atom in supports[node])
    return SparseOccurrenceGraph(
        len(supports), len(edges), len(coverable), len(covered), cover_nodes,
        tuple(connectors), retained_nodes, tuple(spanning), cycle_edges,
        retained_edges, source_components, retained_components, before,
        1.0 - len(retained_nodes) / max(1, len(supports)),
        1.0 - len(retained_edges) / max(1, len(edges)),
        covered == coverable, True,
        source_components != 1 or retained_components == 1, False, False)
