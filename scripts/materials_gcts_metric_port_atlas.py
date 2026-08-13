#!/usr/bin/env python3
"""Scale-normalized motif-centre ports for causal recursive GCTS."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple

from materials_gcts_recursive_connections import (
    LocalClusterType, RecursiveConnectionMarking, map_to_prototypes, point_key)

Point = Tuple[float, float, float]
MetricPort = Tuple[LocalClusterType, LocalClusterType, float]


@dataclass(frozen=True)
class MetricPortEvidence:
    positive: int
    total: int


@dataclass(frozen=True)
class MetricPortAtlas:
    scale: float
    distance_digits: int
    prototypes: Tuple[LocalClusterType, ...]
    evidence: Mapping[MetricPort, MetricPortEvidence]
    accepted_ports: frozenset[MetricPort]
    target_color_evidence: Mapping[MetricPort, Counter[str]]
    minimum_positive_support: int
    minimum_purity: float


@dataclass(frozen=True)
class MetricPortProposals:
    votes: Counter[Point]
    target_color_votes: Mapping[Point, Counter[str]]
    accepted_actions: int


def _proposal(parent: Point, source: Point, scale: float) -> Point:
    return tuple(parent[axis] + scale * (source[axis] - parent[axis])
                 for axis in range(3))  # type: ignore[return-value]


def fit_metric_port_atlas(
        positions: Sequence[Point], cluster_types: Sequence[LocalClusterType],
        target_positions: Iterable[Point], scale: float, *,
        parent_indices: Iterable[int] | None = None,
        target_colors: Sequence[object] | None = None,
        distance_digits: int = 5, minimum_positive_support: int = 2,
        minimum_purity: float = .75) -> MetricPortAtlas:
    """Fit ports using exact separation modulo rotation and recursive scale."""
    targets_sequence = tuple(target_positions)
    targets = {point_key(point) for point in targets_sequence}
    colors = ({} if target_colors is None else
              {point_key(point): repr(color) for point, color in
               zip(targets_sequence, target_colors)})
    parents = tuple(range(len(positions)) if parent_indices is None
                    else parent_indices)
    evidence = defaultdict(lambda: [0, 0])
    color_evidence = defaultdict(Counter)
    for parent in parents:
        for source, source_point in enumerate(positions):
            if parent == source:
                continue
            port = (cluster_types[parent], cluster_types[source],
                    round(math.dist(positions[parent], source_point),
                          distance_digits))
            proposed = point_key(_proposal(
                positions[parent], source_point, scale))
            evidence[port][1] += 1
            evidence[port][0] += proposed in targets
            if proposed in colors:
                color_evidence[port][colors[proposed]] += 1
    frozen = {port: MetricPortEvidence(*counts)
              for port, counts in evidence.items()}
    accepted = frozenset(port for port, item in frozen.items()
                         if item.positive >= minimum_positive_support and
                         item.positive / item.total >= minimum_purity)
    return MetricPortAtlas(
        scale, distance_digits, tuple(sorted(set(cluster_types))), frozen,
        accepted, dict(color_evidence), minimum_positive_support,
        minimum_purity)


def propose_with_metric_ports(
        atlas: MetricPortAtlas, positions: Sequence[Point],
        cluster_types: Sequence[LocalClusterType], *, level_scale: float = 1.0,
        parent_indices: Iterable[int] | None = None) -> MetricPortProposals:
    """Apply frozen ports; the output position is never queried for scoring."""
    mapped = map_to_prototypes(cluster_types, atlas.prototypes)
    parents = tuple(range(len(positions)) if parent_indices is None
                    else parent_indices)
    votes: Counter[Point] = Counter()
    colors = defaultdict(Counter)
    actions = 0
    for parent in parents:
        for source, source_point in enumerate(positions):
            if parent == source:
                continue
            port = (mapped[parent], mapped[source], round(
                math.dist(positions[parent], source_point) / level_scale,
                atlas.distance_digits))
            if port not in atlas.accepted_ports:
                continue
            actions += 1
            proposed = point_key(_proposal(
                positions[parent], source_point, atlas.scale))
            votes[proposed] += 1
            evidence = atlas.target_color_evidence.get(port)
            if evidence:
                maximum = max(evidence.values())
                colors[proposed][min(color for color, count in evidence.items()
                                     if count == maximum)] += 1
    return MetricPortProposals(votes, dict(colors), actions)
