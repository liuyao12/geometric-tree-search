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
        maximum_roles: int = 3, occupied_positions=(),
        occupied_species=()):
    """Describe every candidate using invariant local port-incidence tokens.

    Coordinates select neighbors and provide pair distances only.  No absolute
    position, global frame, point identity, target atom, or material label is
    serialized into a token.
    """
    if (len(occupied_positions) != len(occupied_species) or
            distance_scale <= 0 or neighborhood_reach <= 0 or
            distance_bin_width <= 0 or maximum_neighbors < 1 or
            maximum_roles < 1):
        raise ValueError("invalid incidence descriptor settings")
    points = tuple(sorted(proposals.votes))
    roles = {point: _top_roles(proposals, point, maximum_roles)
             for point in points}
    cell_size = neighborhood_reach * distance_scale
    cells = defaultdict(list)
    for point in points:
        cell = tuple(math.floor(value / cell_size) for value in point)
        cells[cell].append(point)

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
        occupied = sorted(
            ((math.dist(point, other), str(species))
             for other, species in zip(occupied_positions, occupied_species)
             if math.dist(point, other) <= cell_size + 1e-12),
            key=lambda row: (row[0], row[1]))
        tokens.add(("occupied-count", _bucket(len(occupied))))
        for rank, (distance, species) in enumerate(
                occupied[:maximum_neighbors]):
            distance_bin = round(
                distance / (distance_scale * distance_bin_width))
            tokens.add(("occupied-shell", rank, species, distance_bin))
            tokens.add(("occupied-shell-colorless", rank, distance_bin))
        # Radial shells alone conflate distinct angular environments.  The
        # colored metric graph of the nearest occupied neighbors is a proper-
        # motion invariant angular surrogate and does not require a global
        # frame or a lattice axis.
        nearest = sorted(
            ((math.dist(point, other), str(species), tuple(other))
             for other, species in zip(occupied_positions, occupied_species)
             if math.dist(point, other) <= cell_size + 1e-12),
            key=lambda row: (row[0], row[1], row[2]))[:maximum_neighbors]
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
