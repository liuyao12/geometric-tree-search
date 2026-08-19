#!/usr/bin/env python3
"""Canonical typed graph of bounded target-free child-frontier actions."""

from __future__ import annotations

import hashlib
import itertools
import math
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence


Point = tuple[float, float, float]


@dataclass(frozen=True, order=True)
class ChildFrontierNode:
    action_color: str
    channel_code: tuple[int, ...]
    vote_bin: int
    probability_bin: int
    incoming_roles: tuple[Hashable, ...]
    incoming_mass_bin: int
    outgoing_roles: tuple[Hashable, ...]
    outgoing_mass_bin: int
    outgoing_colors: tuple[str, ...]
    dead_end: bool


@dataclass(frozen=True, order=True)
class ChildFrontierEdge:
    left_index: int
    right_index: int
    separation_bin: int
    compatible: bool
    shared_incoming_roles_bin: int
    shared_outgoing_sites_bin: int
    conflicting_outgoing_colors_bin: int
    connection_witnessed: bool


@dataclass(frozen=True)
class ChildFrontierAction:
    node: ChildFrontierNode
    point: Point
    outgoing_sites: tuple[tuple[Point, str], ...]


@dataclass(frozen=True)
class ChildFrontierGraph:
    nodes: tuple[ChildFrontierNode, ...]
    edges: tuple[ChildFrontierEdge, ...]
    compatible_edges: int
    conflict_edges: int
    maximum_compatible_actions: int
    canonical_digest: str
    proper_se3_invariant: bool = True
    lattice_coordinates_used: bool = False
    target_used: bool = False


def count_bin(value: int) -> int:
    value = int(value)
    if value < 0:
        raise ValueError("count bins require nonnegative values")
    return 0 if value == 0 else min(16, int(math.log2(value)) + 1)


def _point(value) -> Point:
    row = tuple(map(float, value))
    if len(row) != 3 or not all(map(math.isfinite, row)):
        raise ValueError("child-frontier positions must be finite 3D points")
    return row  # type: ignore[return-value]


def _site_map(rows):
    result = {}
    for point, color in rows:
        key = tuple(round(value, 6) for value in _point(point))
        prior = result.get(key)
        if prior is not None and prior != str(color):
            raise ValueError("one child frontier predicts two site colors")
        result[key] = str(color)
    return result


def _canonical_incidence(nodes, raw_edges):
    cells = tuple(tuple(index for index, value in enumerate(nodes)
                        if value == node) for node in sorted(set(nodes)))
    permutations = math.prod(math.factorial(len(cell)) for cell in cells)
    if permutations > 40320:
        raise ValueError("child-frontier canonicalization exceeds finite guard")
    canonical_nodes = tuple(sorted(nodes))
    minimum = None
    selected = ()
    for cell_orders in itertools.product(*(
            itertools.permutations(cell) for cell in cells)):
        order = tuple(index for cell in cell_orders for index in cell)
        inverse = {old: new for new, old in enumerate(order)}
        incidence = tuple(sorted(ChildFrontierEdge(
            min(inverse[edge.left_index], inverse[edge.right_index]),
            max(inverse[edge.left_index], inverse[edge.right_index]),
            edge.separation_bin, edge.compatible,
            edge.shared_incoming_roles_bin,
            edge.shared_outgoing_sites_bin,
            edge.conflicting_outgoing_colors_bin,
            edge.connection_witnessed) for edge in raw_edges))
        code = canonical_nodes, incidence
        if minimum is None or code < minimum:
            minimum, selected = code, incidence
    return canonical_nodes, selected


def _maximum_compatible_set(node_count, edges):
    conflicts = {(edge.left_index, edge.right_index) for edge in edges
                 if not edge.compatible}
    for width in range(node_count, 0, -1):
        for subset in itertools.combinations(range(node_count), width):
            if all((left, right) not in conflicts
                   for left, right in itertools.combinations(subset, 2)):
                return width
    return 0


def child_frontier_graph(
        actions: Sequence[ChildFrontierAction], *, minimum_distance: float,
        distance_scale: float, distance_bin_width: float = .25,
        ) -> ChildFrontierGraph:
    rows = tuple(actions)
    if (not rows or len(rows) > 8 or minimum_distance <= 0
            or distance_scale <= 0 or distance_bin_width <= 0
            or not math.isfinite(
                minimum_distance * distance_scale * distance_bin_width)):
        raise ValueError("invalid bounded child-frontier graph inputs")
    points = tuple(_point(row.point) for row in rows)
    if len(set(points)) != len(points):
        raise ValueError("child-frontier action points must be unique")
    site_maps = tuple(_site_map(row.outgoing_sites) for row in rows)
    quantum = distance_scale * distance_bin_width
    raw_edges = []
    for left, right in itertools.combinations(range(len(rows)), 2):
        shared_keys = set(site_maps[left]) & set(site_maps[right])
        conflicts = sum(site_maps[left][key] != site_maps[right][key]
                        for key in shared_keys)
        incoming_left = set(rows[left].node.incoming_roles)
        incoming_right = set(rows[right].node.incoming_roles)
        separation = math.dist(points[left], points[right])
        compatible = separation >= minimum_distance - 1e-8 and conflicts == 0
        shared_incoming = len(incoming_left & incoming_right)
        shared_outgoing = len(shared_keys)
        raw_edges.append(ChildFrontierEdge(
            left, right, int(round(separation / quantum)), compatible,
            count_bin(shared_incoming), count_bin(shared_outgoing),
            count_bin(conflicts), bool(shared_incoming or shared_outgoing)))
    nodes, edges = _canonical_incidence(
        tuple(row.node for row in rows), tuple(raw_edges))
    compatible = sum(edge.compatible for edge in edges)
    conflicts = len(edges) - compatible
    maximum = _maximum_compatible_set(len(nodes), edges)
    code = nodes, edges, compatible, conflicts, maximum
    return ChildFrontierGraph(
        nodes, edges, compatible, conflicts, maximum,
        hashlib.sha256(repr(code).encode()).hexdigest())


def child_frontier_graph_embedding(
        graph: ChildFrontierGraph, *, interaction_order: int = 2,
        ) -> tuple[tuple[Hashable, float], ...]:
    """Sparse ID-free graph colors for a bounded pairwise value model."""
    if interaction_order not in (1, 2) or graph.target_used:
        raise ValueError("invalid child-frontier graph embedding")
    features = Counter()
    for node in graph.nodes:
        coarse = (node.action_color, node.channel_code,
                  node.incoming_mass_bin, node.outgoing_mass_bin,
                  node.dead_end)
        features[("node", node)] += 1
        features[("node-coarse", coarse)] += 1
        features[("incoming-role-set", node.action_color,
                  node.incoming_roles)] += 1
        features[("outgoing-role-set", node.action_color,
                  node.outgoing_roles)] += 1
    for edge in graph.edges:
        left, right = graph.nodes[edge.left_index], graph.nodes[edge.right_index]
        edge_state = (
            edge.separation_bin, edge.compatible,
            edge.shared_incoming_roles_bin, edge.shared_outgoing_sites_bin,
            edge.conflicting_outgoing_colors_bin,
            edge.connection_witnessed)
        features[("edge", tuple(sorted((left, right))), edge_state)] += 1
        features[("edge-coarse", tuple(sorted((left.action_color,
                                                right.action_color))),
                  edge_state)] += 1
    features[("global", count_bin(len(graph.nodes)),
              count_bin(graph.compatible_edges),
              count_bin(graph.conflict_edges),
              graph.maximum_compatible_actions)] += 1
    if interaction_order == 2:
        incident = [[] for _ in graph.nodes]
        for edge in graph.edges:
            state = (edge.separation_bin, edge.compatible,
                     edge.shared_incoming_roles_bin,
                     edge.shared_outgoing_sites_bin,
                     edge.conflicting_outgoing_colors_bin,
                     edge.connection_witnessed)
            incident[edge.left_index].append((
                state, graph.nodes[edge.right_index].action_color,
                graph.nodes[edge.right_index].channel_code))
            incident[edge.right_index].append((
                state, graph.nodes[edge.left_index].action_color,
                graph.nodes[edge.left_index].channel_code))
        for node, messages in zip(graph.nodes, incident):
            features[("message", node.action_color, node.channel_code,
                      tuple(sorted(messages)))] += 1
    return tuple(sorted(((key, float(value)) for key, value in features.items()),
                        key=lambda row: repr(row[0])))


__all__ = [
    "ChildFrontierAction", "ChildFrontierEdge", "ChildFrontierGraph",
    "ChildFrontierNode", "child_frontier_graph",
    "child_frontier_graph_embedding", "count_bin"]
