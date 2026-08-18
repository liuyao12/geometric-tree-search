#!/usr/bin/env python3
"""Typed proper-motion-invariant ports between partial irregular supports."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_supports import SpeciesKey, _species_key
from materials_gcts_partial_irregular_section import PartialIrregularSection


Point = tuple[float, float, float]


@dataclass(frozen=True, order=True)
class PartialPortNode:
    support_type_id: int
    action_species: SpeciesKey
    matched_atoms: int
    prototype_atoms: int
    training_group_support: int


@dataclass(frozen=True, order=True)
class PartialPortEdge:
    endpoint_types: tuple[PartialPortNode, PartialPortNode]
    shared_species: tuple[tuple[SpeciesKey, int], ...]
    separation_bin: int
    shared_distance_profiles: tuple[
        tuple[SpeciesKey, tuple[int, int]], ...]
    chirality: int


@dataclass(frozen=True)
class PartialIrregularPortGraph:
    nodes: tuple[PartialPortNode, ...]
    edges: tuple[PartialPortEdge, ...]
    isolated_nodes: int
    canonical_digest: str
    proper_se3_invariant: bool = True
    lattice_coordinates_used: bool = False
    target_used: bool = False


def _points(rows: Sequence[Sequence[float]]) -> tuple[Point, ...]:
    points = tuple(tuple(map(float, row)) for row in rows)
    if any(len(point) != 3 or not all(map(math.isfinite, point))
           for point in points):
        raise ValueError("port-graph points must be finite 3D vectors")
    return points  # type: ignore[return-value]


def _sub(left: Point, right: Point) -> Point:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _det(first: Point, second: Point, third: Point) -> float:
    return (first[0] * (second[1] * third[2] - second[2] * third[1])
            - first[1] * (second[0] * third[2] - second[2] * third[0])
            + first[2] * (second[0] * third[1] - second[1] * third[0]))


def partial_irregular_port_graph(
        section: PartialIrregularSection,
        occupied_positions: Sequence[Sequence[float]],
        occupied_species: Sequence[Hashable],
        action_positions: Sequence[Sequence[float]],
        action_species: Sequence[Hashable],
        *, distance_scale: float, distance_bin_width: float = .25,
        ) -> PartialIrregularPortGraph:
    occupied = _points(occupied_positions)
    actions = _points(action_positions)
    colors = tuple(_species_key(value) for value in occupied_species)
    action_colors = tuple(_species_key(value) for value in action_species)
    if (len(occupied) != len(colors) or len(actions) != len(action_colors)
            or len(actions) != len(section.action_matches)
            or not actions or distance_scale <= 0
            or distance_bin_width <= 0
            or not math.isfinite(distance_scale * distance_bin_width)):
        raise ValueError("invalid partial port-graph inputs")
    limit = len(occupied)
    nodes_by_action = tuple(PartialPortNode(
        match.prototype_type_id, action_colors[index], match.matched_atoms,
        match.prototype_atoms, match.training_group_support)
        for index, match in enumerate(section.action_matches))
    occupied_by_action = tuple(tuple(sorted(
        index for index in match.matched_target_indices if index < limit))
        for match in section.action_matches)
    edges = []
    incident = set()
    quantum = distance_scale * distance_bin_width
    for left in range(len(actions)):
        for right in range(left + 1, len(actions)):
            shared = tuple(sorted(set(occupied_by_action[left]) &
                                  set(occupied_by_action[right])))
            if not shared:
                continue
            left_node, right_node = nodes_by_action[left], nodes_by_action[right]
            if right_node < left_node:
                oriented_left, oriented_right = right, left
                endpoint_types = (right_node, left_node)
            else:
                oriented_left, oriented_right = left, right
                endpoint_types = (left_node, right_node)
            shared_species = tuple(sorted(Counter(
                colors[index] for index in shared).items()))
            profiles = tuple(sorted((colors[index], tuple(sorted((
                int(round(math.dist(actions[oriented_left], occupied[index]) /
                          quantum)),
                int(round(math.dist(actions[oriented_right], occupied[index]) /
                          quantum)))))) for index in shared))

            # A signed local volume is meaningful only when endpoint identity
            # and the first two shared sites have invariant, distinct roles.
            chirality = 0
            keyed_shared = sorted((
                (colors[index],
                 int(round(math.dist(actions[oriented_left], occupied[index]) /
                           quantum)),
                 int(round(math.dist(actions[oriented_right], occupied[index]) /
                           quantum))), index) for index in shared)
            if (left_node != right_node and len(keyed_shared) >= 2
                    and keyed_shared[0][0] != keyed_shared[1][0]):
                first, second = keyed_shared[0][1], keyed_shared[1][1]
                volume = _det(
                    _sub(actions[oriented_right], actions[oriented_left]),
                    _sub(occupied[first], actions[oriented_left]),
                    _sub(occupied[second], actions[oriented_left]))
                epsilon = 1e-10 * distance_scale ** 3
                chirality = int(volume > epsilon) - int(volume < -epsilon)
            edges.append(PartialPortEdge(
                endpoint_types, shared_species,
                int(round(math.dist(actions[left], actions[right]) / quantum)),
                profiles, chirality))
            incident.update((left, right))
    nodes = tuple(sorted(nodes_by_action))
    edge_rows = tuple(sorted(edges))
    code = (nodes, edge_rows)
    return PartialIrregularPortGraph(
        nodes, edge_rows, len(actions) - len(incident),
        hashlib.sha256(repr(code).encode()).hexdigest())
