#!/usr/bin/env python3
"""Finite ID-free marking for joint local port-incidence geometry."""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from materials_gcts_port_incidence_search import semantic_port_role


@dataclass(frozen=True)
class CandidateIncidenceDescriptor:
    tokens: tuple[Hashable, ...]


@dataclass(frozen=True)
class IncidenceTokenExample:
    group: Hashable
    descriptor: CandidateIncidenceDescriptor
    successful: bool


@dataclass(frozen=True)
class TokenEvidence:
    positive: int
    total: int
    independent_groups: int


@dataclass(frozen=True)
class FrozenIncidenceTokenMarking:
    intercept: float
    token_weights: Mapping[Hashable, float]
    token_evidence: Mapping[Hashable, TokenEvidence]
    minimum_support: int
    minimum_groups: int
    shrinkage: float


def incidence_marking_digest(marking: FrozenIncidenceTokenMarking) -> str:
    """Return a process-stable digest of a frozen token marking."""
    weights = tuple(sorted(
        marking.token_weights.items(), key=lambda row: repr(row[0])))
    evidence = tuple(sorted(
        ((token, row.positive, row.total, row.independent_groups)
         for token, row in marking.token_evidence.items()),
        key=lambda row: repr(row[0])))
    payload = (marking.intercept, weights, evidence,
               marking.minimum_support, marking.minimum_groups,
               marking.shrinkage)
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def _bucket(value: int) -> int:
    return 0 if value <= 0 else min(8, int(math.log2(value)) + 1)


def _top_roles(proposals, point, maximum=3):
    return tuple(sorted(
        ((semantic_port_role(state), int(count))
         for state, count in proposals.state_votes.get(point, {}).items()),
        key=lambda row: (-row[1], row[0]))[:maximum])


def candidate_incidence_descriptors(
        proposals, *, distance_scale: float, neighborhood_reach: float = 3.,
        distance_bin_width: float = .5, maximum_neighbors: int = 8,
        maximum_roles: int = 3, joint_role_geometry: bool = False,
        oriented_port_geometry: bool = False,
        angular_bin_width: float = .25,
        message_passing_rounds: int = 0,
        message_distance_divisor: int = 1,
        message_role_mode: str = "exact",
        message_encoding: str = "exact",
        occupied_positions=(),
        occupied_species=()):
    """Describe every candidate using invariant local port-incidence tokens.

    Coordinates select neighbors and provide pair distances only.  No absolute
    position, global frame, point identity, target atom, or material label is
    serialized into a token.
    """
    if (len(occupied_positions) != len(occupied_species) or
            distance_scale <= 0 or neighborhood_reach <= 0 or
            distance_bin_width <= 0 or maximum_neighbors < 1 or
            maximum_roles < 1 or angular_bin_width <= 0 or
            not 0 <= message_passing_rounds <= 3 or
            not 1 <= message_distance_divisor <= 8 or
            message_role_mode not in {"exact", "coarse", "colors"} or
            message_encoding not in {"exact", "incidence"} or
            (message_encoding == "incidence" and
             message_passing_rounds > 1)):
        raise ValueError("invalid incidence descriptor settings")
    points = tuple(sorted(proposals.votes))
    roles = {point: _top_roles(proposals, point, maximum_roles)
             for point in points}
    cell_size = neighborhood_reach * distance_scale
    cells = defaultdict(list)
    for point in points:
        cell = tuple(math.floor(value / cell_size) for value in point)
        cells[cell].append(point)
    occupied_cells = defaultdict(list)
    for position, species in zip(occupied_positions, occupied_species):
        position = tuple(position)
        cell = tuple(math.floor(value / cell_size) for value in position)
        occupied_cells[cell].append((position, str(species)))

    result = {}
    offsets = tuple((x, y, z) for x in (-1, 0, 1)
                    for y in (-1, 0, 1) for z in (-1, 0, 1))
    for point in points:
        own_role_rows = roles[point]
        own_roles = tuple(role for role, _count in own_role_rows)
        source = proposals.color_votes.get(point, {})
        predicted = proposals.target_color_votes.get(point, {})
        parents = proposals.parent_votes.get(point, {})
        tokens = {
            ("vote", _bucket(proposals.votes[point])),
            ("parent-multiplicity", _bucket(len(parents))),
            ("source-colors", tuple(sorted(source))),
            # These are colors predicted by the frozen connection marking,
            # not colors read from a scoring/held-out target.
            ("predicted-colors", tuple(sorted(predicted))),
        }
        tokens.update(("role", role) for role in own_roles)
        tokens.update(("coarse-role", role.parent_color, role.source_color,
                       role.separation_bin) for role in own_roles)
        tokens.update(("role-support", role.parent_color, role.source_color,
                       _bucket(count)) for role, count in own_role_rows)
        for left_index, left in enumerate(own_roles):
            for right in own_roles[left_index + 1:]:
                tokens.add(("same-site-role-pair", left, right))
        base_cell = tuple(math.floor(value / cell_size) for value in point)
        neighbors = []
        for offset in offsets:
            cell = tuple(base_cell[axis] + offset[axis]
                         for axis in range(3))
            for other in cells.get(cell, ()):
                if other == point:
                    continue
                distance = math.dist(point, other)
                if distance <= cell_size + 1e-12:
                    neighbors.append((distance, other))
        neighbors.sort(key=lambda row: (row[0], row[1]))
        for distance, other in neighbors[:maximum_neighbors]:
            distance_bin = round(
                distance / (distance_scale * distance_bin_width))
            other_roles = tuple(role for role, _count in roles[other])
            if own_roles and other_roles:
                tokens.add(("neighbor-role", own_roles[0],
                            other_roles[0], distance_bin))
            tokens.add(("neighbor-colors",
                        tuple(sorted(predicted)),
                        tuple(sorted(proposals.target_color_votes.get(
                        other, {}))), distance_bin))
        nearby_occupied = []
        for offset in offsets:
            cell = tuple(base_cell[axis] + offset[axis]
                         for axis in range(3))
            for other, species in occupied_cells.get(cell, ()):
                distance = math.dist(point, other)
                if distance <= cell_size + 1e-12:
                    nearby_occupied.append((distance, species, other))
        occupied = sorted(
            ((distance, species)
             for distance, species, _other in nearby_occupied),
            key=lambda row: (row[0], row[1]))
        tokens.add(("occupied-count", _bucket(len(occupied))))
        for rank, (distance, species) in enumerate(
                occupied[:maximum_neighbors]):
            distance_bin = round(
                distance / (distance_scale * distance_bin_width))
            tokens.add(("occupied-shell", rank, species, distance_bin))
            tokens.add(("occupied-shell-colorless", rank, distance_bin))
            if joint_role_geometry and own_roles:
                tokens.add(("role-occupied-shell", own_roles[0], rank,
                            species, distance_bin))
        # Radial shells alone conflate distinct angular environments.  The
        # colored metric graph of the nearest occupied neighbors is a proper-
        # motion invariant angular surrogate and does not require a global
        # frame or a lattice axis.
        nearest = sorted(nearby_occupied,
                         key=lambda row: (row[0], row[1], row[2]))[
                             :maximum_neighbors]
        if oriented_port_geometry:
            # The proposal direction relative to already occupied atoms is
            # the missing pose channel.  Dot products and signed scalar
            # triple products quotient global proper rotation and
            # translation while preserving genuinely different attachment
            # orientations and chirality.  Parent indices refer only to the
            # public occupied seed, never a held-out target.
            axes = []
            for parent_index, multiplicity in sorted(
                    parents.items(), key=lambda row: (-row[1], row[0])):
                if not 0 <= parent_index < len(occupied_positions):
                    raise ValueError("proposal parent index is outside seed")
                vector = tuple(point[axis] -
                               occupied_positions[parent_index][axis]
                               for axis in range(3))
                norm = math.sqrt(sum(value * value for value in vector))
                if norm > 1e-12:
                    axes.append((tuple(value / norm for value in vector),
                                 _bucket(int(multiplicity))))
            axes = axes[:maximum_roles]
            neighbor_axes = []
            for radius, species, neighbor in nearest:
                if radius <= 1e-12:
                    continue
                neighbor_axes.append((
                    tuple((neighbor[axis] - point[axis]) / radius
                          for axis in range(3)), species,
                    round(radius / (distance_scale * distance_bin_width))))
            for axis, multiplicity in axes:
                tokens.add(("port-axis-multiplicity", multiplicity))
                for neighbor_axis, species, radius_bin in neighbor_axes:
                    cosine = sum(axis[index] * neighbor_axis[index]
                                 for index in range(3))
                    tokens.add(("port-neighbor-angle", species, radius_bin,
                                round(cosine / angular_bin_width)))
                    if own_roles:
                        tokens.add(("role-port-neighbor-angle", own_roles[0],
                                    species, radius_bin,
                                    round(cosine / angular_bin_width)))
            for left in range(len(axes)):
                for right in range(left + 1, len(axes)):
                    cosine = sum(axes[left][0][axis] * axes[right][0][axis]
                                 for axis in range(3))
                    tokens.add(("port-axis-angle",
                                round(cosine / angular_bin_width)))
            if len(axes) >= 3:
                left, middle, right = (axes[index][0] for index in range(3))
                cross = (middle[1] * right[2] - middle[2] * right[1],
                         middle[2] * right[0] - middle[0] * right[2],
                         middle[0] * right[1] - middle[1] * right[0])
                handedness = sum(left[index] * cross[index]
                                 for index in range(3))
                tokens.add(("port-axis-handedness",
                            round(handedness / angular_bin_width)))
        node_colors = tuple((species, round(round(
            radius / (distance_scale * distance_bin_width)) /
            message_distance_divisor))
            for radius, species, _neighbor in nearest)
        edge_bins = {(left, right): round(round(math.dist(
            nearest[left][2], nearest[right][2]) /
            (distance_scale * distance_bin_width)) /
            message_distance_divisor)
            for left in range(len(nearest))
            for right in range(left + 1, len(nearest))}
        for left_index, (left_radius, left_species, left_point) in enumerate(
                nearest):
            for right_radius, right_species, right_point in nearest[
                    left_index + 1:]:
                radii = tuple(sorted((
                    round(left_radius /
                          (distance_scale * distance_bin_width)),
                    round(right_radius /
                          (distance_scale * distance_bin_width)))))
                species_pair = tuple(sorted((left_species, right_species)))
                pair_bin = round(math.dist(left_point, right_point) /
                                 (distance_scale * distance_bin_width))
                tokens.add(("occupied-metric-edge", species_pair,
                            radii, pair_bin))
                if joint_role_geometry and own_roles:
                    tokens.add(("role-occupied-metric-edge", own_roles[0],
                                species_pair, radii, pair_bin))
        if own_roles:
            primary = own_roles[0]
            message_role = primary if message_role_mode == "exact" else (
                primary.parent_color, primary.source_color,
                primary.separation_bin) if message_role_mode == "coarse" \
                else (primary.parent_color, primary.source_color)
        if message_encoding == "exact":
            for message_round in range(1, message_passing_rounds + 1):
                refined = []
                for node, color in enumerate(node_colors):
                    messages = tuple(sorted(((
                        edge_bins[min(node, other), max(node, other)],
                        node_colors[other])
                        for other in range(len(node_colors))
                        if other != node), key=repr))
                    refined.append(hashlib.sha256(repr(
                        (color, messages)).encode()).hexdigest()[:20])
                node_colors = tuple(refined)
                if own_roles:
                    tokens.update(("role-occupied-message-node",
                                   message_round, message_role, color)
                                  for color in node_colors)
                    tokens.add(("role-occupied-message-graph",
                                message_round, message_role,
                                tuple(sorted(node_colors))))
        elif message_passing_rounds and own_roles:
            # Finite additive quotient of one Weisfeiler-Lehman incidence
            # round.  It retains colored radial node states and all colored
            # metric-edge messages, but replaces the near-unique hash of an
            # entire neighborhood with bounded multiplicity tokens.  Exact
            # action geometry remains outside this marking and is unchanged.
            node_counts = Counter(node_colors)
            edge_counts = Counter()
            for (left, right), edge_bin in edge_bins.items():
                states = tuple(sorted(
                    (node_colors[left], node_colors[right]), key=repr))
                edge_counts[(states, edge_bin)] += 1
            tokens.update(("role-occupied-message-node", 1,
                           message_role, state, _bucket(count))
                          for state, count in node_counts.items())
            tokens.update(("role-occupied-message-edge", 1,
                           message_role, states, edge_bin, _bucket(count))
                          for (states, edge_bin), count in edge_counts.items())
            species_counts = Counter(state[0] for state in node_colors)
            tokens.add(("role-occupied-message-graph", 1, message_role,
                        _bucket(len(node_colors)), _bucket(len(edge_bins)),
                        tuple(sorted((species, _bucket(count))
                                     for species, count
                                     in species_counts.items()))))
        result[point] = CandidateIncidenceDescriptor(
            tuple(sorted(tokens, key=repr)))
    return result


def fit_incidence_token_marking(
        examples: Sequence[IncidenceTokenExample], *, minimum_support: int = 8,
        minimum_groups: int = 2, shrinkage: float = .5,
        smoothing: float = 1.) -> FrozenIncidenceTokenMarking:
    if (not examples or minimum_support < 1 or minimum_groups < 1 or
            shrinkage <= 0 or smoothing <= 0 or
            not any(row.successful for row in examples) or
            all(row.successful for row in examples)):
        raise ValueError("token marking needs both labels and valid settings")
    positive = sum(row.successful for row in examples)
    negative = len(examples) - positive
    prior = (positive + smoothing) / (len(examples) + 2 * smoothing)
    intercept = math.log(prior / (1 - prior))
    counts = defaultdict(lambda: [0, 0, set()])
    for row in examples:
        for token in set(row.descriptor.tokens):
            counts[token][0] += int(row.successful)
            counts[token][1] += 1
            counts[token][2].add(row.group)
    evidence = {
        token: TokenEvidence(pos, total, len(groups))
        for token, (pos, total, groups) in counts.items()}
    weights = {}
    for token, item in evidence.items():
        if item.total < minimum_support or \
                item.independent_groups < minimum_groups:
            continue
        token_probability = (item.positive + smoothing) / (
            item.total + 2 * smoothing)
        logit = math.log(token_probability / (1 - token_probability))
        weights[token] = max(-4., min(4., shrinkage * (logit - intercept)))
    return FrozenIncidenceTokenMarking(
        intercept, weights, evidence, minimum_support, minimum_groups,
        shrinkage)


def score_incidence_descriptor(
        marking: FrozenIncidenceTokenMarking,
        descriptor: CandidateIncidenceDescriptor) -> float:
    weights = tuple(marking.token_weights[token]
                    for token in descriptor.tokens
                    if token in marking.token_weights)
    value = marking.intercept + (sum(weights) / math.sqrt(len(weights))
                                 if weights else 0.)
    if value >= 0:
        inverse = math.exp(-min(value, 50.))
        return 1. / (1. + inverse)
    exponential = math.exp(max(value, -50.))
    return exponential / (1. + exponential)


def score_incidence_descriptor_by_channel(
        marking: FrozenIncidenceTokenMarking,
        descriptor: CandidateIncidenceDescriptor) -> float:
    """Score a low-rank projection with one vote per token family.

    A family is the first field of a descriptor token (for example ``role``,
    ``neighbor-role``, or ``occupied-metric-edge``). Averaging within a family
    prevents a large rotation/edge orbit from receiving extra weight merely
    because it has more discrete representatives. Exact candidate geometry
    and train-frozen token evidence are unchanged.
    """
    families = defaultdict(list)
    for token in descriptor.tokens:
        if token not in marking.token_weights:
            continue
        family = token[0] if isinstance(token, tuple) and token else token
        families[family].append(marking.token_weights[token])
    values = tuple(sum(rows) / len(rows) for rows in families.values())
    value = marking.intercept + (sum(values) / math.sqrt(len(values))
                                 if values else 0.)
    if value >= 0:
        inverse = math.exp(-min(value, 50.))
        return 1. / (1. + inverse)
    exponential = math.exp(max(value, -50.))
    return exponential / (1. + exponential)
