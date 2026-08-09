#!/usr/bin/env python3
"""Finite GCTS markings for recursively inflated clusters of clusters.

The atoms in a bounded configuration are treated as centres of local colored
clusters.  A higher-order action connects a ``parent`` cluster to a ``source``
cluster and proposes the affine image

    parent + scale * (source - parent).

The marking is a finite table over the two local cluster types and a binned,
scale-normalized separation.  It therefore contains no lattice coordinates,
material names, physical potential, or preferred orientation.  When several
accepted actions propose the same site, their multiplicity is an overlap
consensus score for the covering/tree search.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Hashable, Iterable, Mapping, Sequence, Tuple

Point = Tuple[float, float, float]


@dataclass(frozen=True, order=True)
class LocalClusterType:
    color_key: str
    cumulative_neighbor_counts: Tuple[int, ...]


@dataclass(frozen=True, order=True)
class RecursiveConnectionState:
    parent_type: LocalClusterType
    source_type: LocalClusterType
    normalized_separation_bin: int


@dataclass(frozen=True)
class StateEvidence:
    positive: int
    total: int


@dataclass(frozen=True)
class RecursiveConnectionMarking:
    scale: float
    separation_bin_width: float
    prototypes: Tuple[LocalClusterType, ...]
    evidence: Mapping[RecursiveConnectionState, StateEvidence]
    accepted_states: frozenset[RecursiveConnectionState]
    minimum_positive_support: int
    minimum_purity: float


@dataclass(frozen=True)
class MarkedProposalResult:
    votes: Counter[Point]
    accepted_pair_actions: int
    true_pair_actions: int | None
    color_votes: Mapping[Point, Counter[str]]
    state_votes: Mapping[Point, Counter[RecursiveConnectionState]]


def point_key(point: Sequence[float], digits: int = 6) -> Point:
    return tuple(round(float(value), digits) for value in point)  # type: ignore[return-value]


def local_cluster_types(
        positions: Sequence[Point], colors: Sequence[Hashable],
        radial_edges: Sequence[float]) -> Tuple[LocalClusterType, ...]:
    """Encode rotation-free local colored clusters by radial neighbor counts."""
    if len(positions) != len(colors) or not positions:
        raise ValueError("positions and colors must be nonempty and aligned")
    edges = tuple(float(edge) for edge in radial_edges)
    if not edges or any(left >= right for left, right in zip(edges, edges[1:])):
        raise ValueError("radial edges must be strictly increasing")
    color_keys = tuple(sorted({repr(color) for color in colors}))
    encoded_colors = tuple(repr(color) for color in colors)
    result = []
    for center_index, center in enumerate(positions):
        counts = []
        for color in color_keys:
            separations = [math.dist(center, neighbor)
                           for index, neighbor in enumerate(positions)
                           if index != center_index and encoded_colors[index] == color]
            counts.extend(sum(separation <= edge for separation in separations)
                          for edge in edges)
        result.append(LocalClusterType(
            encoded_colors[center_index], tuple(counts)))
    return tuple(result)


def _nearest_prototype(
        cluster_type: LocalClusterType,
        prototypes_by_color: Mapping[str, Tuple[LocalClusterType, ...]],
        ) -> LocalClusterType:
    candidates = prototypes_by_color.get(cluster_type.color_key)
    if not candidates:
        raise ValueError(f"no prototype for color {cluster_type.color_key}")
    return min(candidates, key=lambda prototype: (
        sum(abs(left - right) for left, right in zip(
            cluster_type.cumulative_neighbor_counts,
            prototype.cumulative_neighbor_counts)), prototype))


def map_to_prototypes(
        cluster_types: Sequence[LocalClusterType],
        prototypes: Sequence[LocalClusterType]) -> Tuple[LocalClusterType, ...]:
    """Map boundary-perturbed clusters to the nearest frozen learned type."""
    by_color: Dict[str, list[LocalClusterType]] = defaultdict(list)
    for prototype in sorted(set(prototypes)):
        by_color[prototype.color_key].append(prototype)
    frozen = {color: tuple(values) for color, values in by_color.items()}
    return tuple(_nearest_prototype(cluster_type, frozen)
                 for cluster_type in cluster_types)


def _proposal(parent: Point, source: Point, scale: float) -> Point:
    return tuple(parent[axis] + scale * (source[axis] - parent[axis])
                 for axis in range(3))  # type: ignore[return-value]


def learn_recursive_connection_marking(
        positions: Sequence[Point], cluster_types: Sequence[LocalClusterType],
        target_positions: Iterable[Point], scale: float,
        separation_bin_width: float = .5,
        minimum_positive_support: int = 2,
        minimum_purity: float = 1.0,
        parent_indices: Iterable[int] | None = None,
        ) -> RecursiveConnectionMarking:
    """Learn a finite connection marking from one known growth transition."""
    if len(positions) != len(cluster_types) or len(positions) < 2:
        raise ValueError("positions and cluster types must be aligned")
    if scale <= 0 or separation_bin_width <= 0:
        raise ValueError("scale and bin width must be positive")
    targets = {point_key(point) for point in target_positions}
    counts: Dict[RecursiveConnectionState, list[int]] = defaultdict(
        lambda: [0, 0])
    parents = tuple(range(len(positions)) if parent_indices is None
                    else parent_indices)
    if not parents or any(index < 0 or index >= len(positions)
                          for index in parents):
        raise ValueError("parent indices must select known positions")
    for parent_index in parents:
        parent = positions[parent_index]
        for source_index, source in enumerate(positions):
            if parent_index == source_index:
                continue
            state = RecursiveConnectionState(
                cluster_types[parent_index], cluster_types[source_index],
                round(math.dist(parent, source) / separation_bin_width))
            counts[state][1] += 1
            counts[state][0] += point_key(_proposal(parent, source, scale)) in targets
    evidence = {state: StateEvidence(positive, total)
                for state, (positive, total) in counts.items()}
    accepted = frozenset(
        state for state, item in evidence.items()
        if item.positive >= minimum_positive_support and
        item.positive / item.total >= minimum_purity)
    return RecursiveConnectionMarking(
        scale, separation_bin_width, tuple(sorted(set(cluster_types))),
        evidence, accepted, minimum_positive_support, minimum_purity)


def propose_with_recursive_marking(
        marking: RecursiveConnectionMarking, positions: Sequence[Point],
        cluster_types: Sequence[LocalClusterType], level_scale: float = 1.0,
        target_positions: Iterable[Point] | None = None,
        parent_indices: Iterable[int] | None = None,
        ) -> MarkedProposalResult:
    """Apply a frozen marking and aggregate overlapping action proposals."""
    if len(positions) != len(cluster_types) or level_scale <= 0:
        raise ValueError("positions/types must align and level scale be positive")
    mapped = map_to_prototypes(cluster_types, marking.prototypes)
    targets = (None if target_positions is None else
               {point_key(point) for point in target_positions})
    votes: Counter[Point] = Counter()
    color_votes: Dict[Point, Counter[str]] = defaultdict(Counter)
    state_votes: Dict[Point, Counter[RecursiveConnectionState]] = defaultdict(
        Counter)
    accepted_pairs = 0
    true_pairs = 0
    parents = tuple(range(len(positions)) if parent_indices is None
                    else parent_indices)
    if not parents or any(index < 0 or index >= len(positions)
                          for index in parents):
        raise ValueError("parent indices must select known positions")
    for parent_index in parents:
        parent = positions[parent_index]
        for source_index, source in enumerate(positions):
            if parent_index == source_index:
                continue
            state = RecursiveConnectionState(
                mapped[parent_index], mapped[source_index],
                round(math.dist(parent, source) /
                      (level_scale * marking.separation_bin_width)))
            if state not in marking.accepted_states:
                continue
            accepted_pairs += 1
            target = point_key(_proposal(parent, source, marking.scale))
            votes[target] += 1
            color_votes[target][mapped[source_index].color_key] += 1
            state_votes[target][state] += 1
            if targets is not None:
                true_pairs += target in targets
    return MarkedProposalResult(
        votes, accepted_pairs, None if targets is None else true_pairs,
        dict(color_votes), dict(state_votes))


def consensus_sites(votes: Counter[Point], minimum_votes: int) -> frozenset[Point]:
    if minimum_votes < 1:
        raise ValueError("minimum votes must be positive")
    return frozenset(point for point, count in votes.items()
                     if count >= minimum_votes)
