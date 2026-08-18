#!/usr/bin/env python3
"""Target-free finite marking of the frontier created by one GCTS action."""

from __future__ import annotations

import math
from collections import Counter

from materials_gcts_incidence_token_marking import CandidateIncidenceDescriptor
from materials_gcts_port_incidence_search import (
    port_incidence_patterns, port_incidence_state)


def _bucket(value):
    return 0 if value <= 0 else min(16, int(math.log2(value)) + 1)


def successor_outgoing_points(
        proposals, *, new_parent_index: int, occupied_positions,
        minimum_distance: float):
    if (new_parent_index < 0 or new_parent_index >= len(occupied_positions) or
            minimum_distance <= 0):
        raise ValueError("invalid successor frontier inputs")
    return tuple(sorted(point for point in proposals.votes
        if new_parent_index in proposals.parent_votes.get(point, {}) and
        not any(math.dist(point, occupied) < minimum_distance - 1e-8
                for occupied in occupied_positions)))


def successor_state_descriptor(
        proposals, *, new_parent_index: int, new_parent_position,
        occupied_positions, minimum_distance: float, distance_scale: float,
        distance_bin_width: float = .5) -> CandidateIncidenceDescriptor:
    """Describe the still-unplaced frontier causally exposed by an action."""
    if (new_parent_index < 0 or new_parent_index >= len(occupied_positions) or
            minimum_distance <= 0 or distance_scale <= 0 or
            distance_bin_width <= 0):
        raise ValueError("invalid successor-state inputs")
    outgoing = successor_outgoing_points(
        proposals, new_parent_index=new_parent_index,
        occupied_positions=occupied_positions,
        minimum_distance=minimum_distance)
    votes = tuple(proposals.votes[point] for point in outgoing)
    parent_mass = tuple(sum(proposals.parent_votes.get(point, {}).values())
                        for point in outgoing)
    state = port_incidence_state(
        proposals, outgoing, maximum_roles=8, minimum_multiplicity=1)
    patterns = port_incidence_patterns(
        proposals, outgoing, maximum_order=2, maximum_patterns=32,
        roles_per_site=4) if outgoing else ()
    distances = Counter(round(math.dist(new_parent_position, point) /
                              (distance_scale * distance_bin_width))
                        for point in outgoing)
    tokens = {
        ("successor-frontier-count", _bucket(len(proposals.votes))),
        ("successor-outgoing-count", _bucket(len(outgoing))),
        ("successor-vote-mass", _bucket(sum(votes))),
        ("successor-max-vote", _bucket(max(votes, default=0))),
        ("successor-parent-mass", _bucket(sum(parent_mass))),
        ("successor-max-parent-mass", _bucket(max(parent_mass, default=0))),
        ("successor-source-colors", tuple(sorted({
            color for point in outgoing
            for color in proposals.color_votes.get(point, {})}))),
        ("successor-predicted-colors", tuple(sorted({
            color for point in outgoing
            for color in proposals.target_color_votes.get(point, {})}))),
    }
    tokens.update(("successor-distance", distance, _bucket(count))
                  for distance, count in distances.items())
    tokens.update(("successor-role", role) for role, _count in state.roles)
    tokens.update(("successor-coarse-role", role.parent_color,
                   role.source_color, role.separation_bin)
                  for role, _count in state.roles)
    tokens.update(("successor-pattern", pattern) for pattern in patterns)
    return CandidateIncidenceDescriptor(tuple(sorted(tokens, key=repr)))


ROLLOUT_TOKEN_FAMILIES = frozenset((
    "successor-frontier-count", "successor-outgoing-count",
    "successor-vote-mass", "successor-max-vote",
    "successor-parent-mass", "successor-max-parent-mass",
    "successor-source-colors", "successor-predicted-colors",
    "successor-distance", "successor-coarse-role"))


def rollout_state_descriptor(
        root: CandidateIncidenceDescriptor,
        branches) -> CandidateIncidenceDescriptor:
    """Aggregate an unordered bounded set of next-successor descriptors."""
    branches = tuple(branches)
    tokens = {("rollout-branch-count", _bucket(len(branches)))}
    tokens.update(("rollout-root", token) for token in root.tokens)
    counts = Counter(token for branch in branches for token in branch.tokens
                     if token[0] in ROLLOUT_TOKEN_FAMILIES)
    tokens.update(("rollout-child-token", token, _bucket(count))
                  for token, count in counts.items())
    summaries = Counter(tuple(token for token in branch.tokens
                              if token[0] in ROLLOUT_TOKEN_FAMILIES)
                        for branch in branches)
    tokens.update(("rollout-child-state", state, _bucket(count))
                  for state, count in summaries.items())
    return CandidateIncidenceDescriptor(tuple(sorted(tokens, key=repr)))
