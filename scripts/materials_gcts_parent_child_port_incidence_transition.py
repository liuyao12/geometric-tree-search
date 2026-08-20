#!/usr/bin/env python3
"""Canonical typed incidence across a parent→child GCTS transition.

The aggregate transition audit retained graph totals but forgot which parent
obligation met which child obligation.  This module keeps that correspondence
as one six-node complete incidence graph.  Parent and child nodes form distinct
color cells; canonicalization quotients only permutations inside each block.
No support/action identifier, lattice coordinate, target atom, translation, or
global frame enters the graph.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_irregular_supports import (
    FrozenSupportVocabulary, _species_key)
from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortNode,
    _canonical_incidence)
from materials_gcts_partial_irregular_section import partial_irregular_section


Point = tuple[float, float, float]


@dataclass(frozen=True)
class FrozenPortTransitionBlock:
    role: str
    nodes: tuple[PartialPortNode, ...]
    action_positions: tuple[Point, ...]
    action_sites: tuple[tuple[tuple[float, float, float], tuple[str, str]], ...]
    matched_sites: tuple[frozenset, ...]
    prototype_tokens: tuple[tuple, ...]


def _points(rows: Sequence[Sequence[float]]) -> tuple[Point, ...]:
    result = tuple(tuple(map(float, row)) for row in rows)
    if any(len(point) != 3 or not all(map(math.isfinite, point))
           for point in result):
        raise ValueError("transition points must be finite 3D vectors")
    return result  # type: ignore[return-value]


def _site_key(point: Point, species: Hashable):
    return tuple(round(value, 8) for value in point), _species_key(species)


def _sub(left: Point, right: Point) -> Point:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _det(first: Point, second: Point, third: Point) -> float:
    return (first[0] * (second[1] * third[2] - second[2] * third[1])
            - first[1] * (second[0] * third[2] - second[2] * third[0])
            + first[2] * (second[0] * third[1] - second[1] * third[0]))


def _prototype_token(prototype, tolerance: float):
    chemistry = tuple(sorted(Counter(prototype.species).items()))
    distances = tuple(sorted(
        int(prototype.quantized_distances[left][right])
        for left in range(len(prototype.species))
        for right in range(left + 1, len(prototype.species))))
    # Geometry, not the train-assigned type ID, names a support.  Tolerance is
    # included so equal integer tables from different schemas cannot alias.
    return chemistry, round(float(tolerance), 12), distances


def port_incidence_transition_block(vocabulary, support, occupied,
                                    occupied_species, actions,
                                    action_species, block):
    """Freeze one block once so many candidate child blocks can reuse it."""
    if block not in ("parent", "child"):
        raise ValueError("transition block role must be parent or child")
    section = partial_irregular_section(
        vocabulary, support, occupied, occupied_species,
        actions, action_species)
    prototypes = {row.type_id: row for row in vocabulary.prototypes}
    sites = tuple(_site_key(point, species) for point, species in zip(
        occupied + actions, tuple(occupied_species) + tuple(action_species)))
    nodes, action_sites, matched_sites, tokens = [], [], [], []
    maximum_support = max(support)
    for match, point, species in zip(
            section.action_matches, actions, action_species):
        prototype = prototypes[match.prototype_type_id]
        token = _prototype_token(prototype, vocabulary.distance_tolerance)
        # ``action_species`` is a semantic node color.  Encoding block,
        # chemistry and support geometry here lets the existing equivariant
        # message learner reuse the graph without ever seeing type IDs.
        color = _species_key((block, _species_key(species), token))
        node = PartialPortNode(
            0, color, match.matched_atoms, match.prototype_atoms,
            max(1, round(10 * match.training_group_support /
                         maximum_support)))
        matched = frozenset(sites[index]
                            for index in match.matched_target_indices)
        nodes.append(node)
        action_sites.append(_site_key(point, species))
        matched_sites.append(matched)
        tokens.append(token)
    return FrozenPortTransitionBlock(
        block, tuple(nodes), tuple(actions), tuple(action_sites),
        tuple(matched_sites), tuple(tokens))


def combine_port_incidence_transition_blocks(
        parent: FrozenPortTransitionBlock,
        child: FrozenPortTransitionBlock, *, distance_scale: float,
        distance_bin_width: float = .25) -> PartialIrregularPortGraph:
    """Combine frozen parent/child blocks into one canonical incidence graph."""
    if (parent.role != "parent" or child.role != "child"
            or len(parent.nodes) != 3 or len(child.nodes) != 3
            or distance_scale <= 0 or distance_bin_width <= 0
            or not math.isfinite(distance_scale * distance_bin_width)):
        raise ValueError("invalid frozen transition blocks")
    rows = tuple(zip(parent.nodes, parent.action_positions,
                     parent.action_sites, parent.matched_sites,
                     parent.prototype_tokens)) + tuple(zip(
                         child.nodes, child.action_positions,
                         child.action_sites, child.matched_sites,
                         child.prototype_tokens))
    nodes = tuple(row[0] for row in rows)
    quantum = distance_scale * distance_bin_width
    raw_edges = []
    witnessed_nodes = set()
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            left_node, left_point, left_action, left_sites, left_token = rows[left]
            right_node, right_point, right_action, right_sites, right_token = rows[right]
            relation = ("parent-parent" if right < 3 else
                        "child-child" if left >= 3 else "parent-child")
            shared = tuple(sorted(left_sites & right_sites, key=repr))
            chemistry = Counter(species for _point, species in shared)
            chemistry[_species_key(("relation", relation))] += 1
            if left_token == right_token:
                chemistry[_species_key(("same-support-geometry", True))] += 1
            left_in_right = left_action in right_sites
            right_in_left = right_action in left_sites
            if relation == "parent-child":
                if left_in_right:
                    chemistry[_species_key((
                        "parent-action-in-child-support", True))] += 1
                if right_in_left:
                    chemistry[_species_key((
                        "child-action-in-parent-support", True))] += 1
            elif left_in_right or right_in_left:
                chemistry[_species_key((
                    "endpoint-actions-in-other-support",
                    int(left_in_right) + int(right_in_left)))] += 1
            profiles = tuple(sorted((species, tuple(sorted((
                int(round(math.dist(left_point, point) / quantum)),
                int(round(math.dist(right_point, point) / quantum))))))
                for point, species in shared))
            chirality = 0
            keyed = sorted((
                (species,
                 int(round(math.dist(left_point, point) / quantum)),
                 int(round(math.dist(right_point, point) / quantum))), point)
                for point, species in shared)
            if len(keyed) >= 2 and keyed[0][0] != keyed[1][0]:
                volume = _det(
                    _sub(right_point, left_point),
                    _sub(keyed[0][1], left_point),
                    _sub(keyed[1][1], left_point))
                epsilon = 1e-10 * distance_scale ** 3
                chirality = int(volume > epsilon) - int(volume < -epsilon)
            witnessed = bool(shared or left_in_right or right_in_left)
            if witnessed:
                witnessed_nodes.update((left, right))
            edge = PartialIncidenceEdge(
                left, right, tuple(sorted(chemistry.items())),
                int(round(math.dist(left_point, right_point) / quantum)),
                profiles, chirality, witnessed)
            raw_edges.append((left, right, edge))
    canonical_nodes, incidence = _canonical_incidence(nodes, tuple(raw_edges))
    code = canonical_nodes, incidence
    return PartialIrregularPortGraph(
        canonical_nodes, (), len(nodes) - len(witnessed_nodes),
        hashlib.sha256(repr(code).encode()).hexdigest(),
        proper_se3_invariant=True, lattice_coordinates_used=False,
        target_used=False, incidence_edges=incidence)


def parent_child_port_incidence_transition(
        vocabulary: FrozenSupportVocabulary,
        training_group_support: Sequence[int],
        parent_occupied_positions: Sequence[Sequence[float]],
        parent_occupied_species: Sequence[Hashable],
        parent_action_positions: Sequence[Sequence[float]],
        parent_action_species: Sequence[Hashable],
        child_occupied_positions: Sequence[Sequence[float]],
        child_occupied_species: Sequence[Hashable],
        child_action_positions: Sequence[Sequence[float]],
        child_action_species: Sequence[Hashable],
        *, distance_scale: float, distance_bin_width: float = .25,
        ) -> PartialIrregularPortGraph:
    """Build a complete, proper-SE(3)-invariant six-node transition graph."""
    parent_occupied = _points(parent_occupied_positions)
    parent_actions = _points(parent_action_positions)
    child_occupied = _points(child_occupied_positions)
    child_actions = _points(child_action_positions)
    support = tuple(map(int, training_group_support))
    if (len(parent_actions) != 3 or len(child_actions) != 3
            or len(parent_occupied) != len(parent_occupied_species)
            or len(parent_actions) != len(parent_action_species)
            or len(child_occupied) != len(child_occupied_species)
            or len(child_actions) != len(child_action_species)
            or len(support) != len(vocabulary.prototypes)
            or any(value < 1 for value in support)
            or distance_scale <= 0 or distance_bin_width <= 0
            or not math.isfinite(distance_scale * distance_bin_width)):
        raise ValueError("invalid parent-child port-incidence transition")
    parent = port_incidence_transition_block(
        vocabulary, support, parent_occupied,
        tuple(parent_occupied_species), parent_actions,
        tuple(parent_action_species), "parent")
    child = port_incidence_transition_block(
        vocabulary, support, child_occupied,
        tuple(child_occupied_species), child_actions,
        tuple(child_action_species), "child")
    return combine_port_incidence_transition_blocks(
        parent, child, distance_scale=distance_scale,
        distance_bin_width=distance_bin_width)
