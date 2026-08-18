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

import itertools
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
    target_color_evidence: Mapping[RecursiveConnectionState, Counter[str]]


@dataclass(frozen=True)
class MarkedProposalResult:
    votes: Counter[Point]
    accepted_pair_actions: int
    true_pair_actions: int | None
    color_votes: Mapping[Point, Counter[str]]
    target_color_votes: Mapping[Point, Counter[str]]
    state_votes: Mapping[Point, Counter[RecursiveConnectionState]]
    parent_votes: Mapping[Point, Counter[int]]
    # Both ordered endpoints are causal dependencies of an affine action.
    # This stays separate from the geometric ``parent_votes`` role because a
    # newly placed source can expose a continuation just as a new parent can.
    causal_endpoint_votes: Mapping[Point, Counter[int]] | None = None


@dataclass(frozen=True)
class RecursiveScaleEstimate:
    scale: float
    one_level_closure: float
    two_level_closure: float
    candidate_scales: int
    learned_from_positions_only: bool


def point_key(point: Sequence[float], digits: int = 6) -> Point:
    return tuple(round(float(value), digits) for value in point)  # type: ignore[return-value]


def infer_recursive_scale(
        positions: Sequence[Point], *, minimum_scale: float = 1.3,
        maximum_scale: float = 2.2, maximum_distance: float | None = None,
        distance_digits: int = 5, minimum_peak_count: int = 30,
        matching_tolerance: float = 1e-3) -> RecursiveScaleEstimate:
    """Infer an inflation from two-level closure of the distance spectrum.

    A genuine recursive scale should map recurrent separations to recurrent
    separations at both ``s`` and ``s**2``. Testing the second power rejects
    accidental ratios that fit only one pair of shells. No target window,
    lattice coordinate, phase label, or chemical potential enters the score.
    """
    if len(positions) < 3 or not 1.0 < minimum_scale < maximum_scale:
        raise ValueError("need three points and a valid scale interval")
    if maximum_distance is None:
        center = tuple(sum(point[axis] for point in positions) / len(positions)
                       for axis in range(3))
        maximum_distance = max(math.dist(center, point) for point in positions)
    spectrum = Counter(
        round(math.dist(left, right), distance_digits)
        for index, left in enumerate(positions)
        for right in positions[index + 1:]
        if 0.0 < math.dist(left, right) <= maximum_distance)
    peaks = tuple((distance, count) for distance, count in spectrum.items()
                  if count >= minimum_peak_count)
    candidates = {
        right / left: False
        for left, _ in peaks for right, _ in peaks
        if minimum_scale <= right / left <= maximum_scale}
    # Recursive scales commonly have a short algebraic description. Add all
    # positive roots of x^2-a*x-b with small integer coefficients; the same
    # closure score, not a named constant, decides whether any is useful.
    for coefficient in range(-4, 5):
        for constant in range(-4, 5):
            discriminant = coefficient * coefficient + 4 * constant
            if discriminant < 0:
                continue
            root = (coefficient + math.sqrt(discriminant)) / 2
            if minimum_scale <= root <= maximum_scale:
                candidates[root] = True
    if not candidates:
        raise ValueError("no recurrent multiscale distance ratio")

    def closure(scale):
        matched = total = 0
        distances = tuple(spectrum)
        for distance, count in peaks:
            target = distance * scale
            if target > maximum_distance:
                continue
            total += count
            nearest = min(distances, key=lambda value: abs(value - target))
            if abs(nearest - target) <= matching_tolerance:
                matched += min(count, spectrum[nearest])
        return matched / max(1, total)

    scored = []
    for scale, algebraic in candidates.items():
        first, second = closure(scale), closure(scale * scale)
        scored.append((min(first, second), first * second, algebraic,
                       -(abs(scale - 1.0)), scale, first, second))
    _, _, _, _, scale, first, second = max(scored)
    return RecursiveScaleEstimate(
        scale, first, second, len(candidates), True)


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
    maximum_edge = edges[-1]
    inverse = 1.0 / maximum_edge
    grid = defaultdict(list)
    for index, point in enumerate(positions):
        cell = tuple(math.floor(value * inverse) for value in point)
        grid[cell].append(index)
    result = []
    for center_index, center in enumerate(positions):
        counts_by_color = {
            color: [0 for _ in edges] for color in color_keys}
        cell = tuple(math.floor(value * inverse) for value in center)
        for offset in itertools.product((-1, 0, 1), repeat=3):
            neighbor_cell = tuple(cell[axis] + offset[axis]
                                  for axis in range(3))
            for index in grid.get(neighbor_cell, ()):
                if index == center_index:
                    continue
                separation = math.dist(center, positions[index])
                if separation > maximum_edge:
                    continue
                color_counts = counts_by_color[encoded_colors[index]]
                for edge_index, edge in enumerate(edges):
                    color_counts[edge_index] += separation <= edge
        counts = [count for color in color_keys
                  for count in counts_by_color[color]]
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


def learn_recurrent_cluster_prototypes(
        cluster_types_by_group: Sequence[Sequence[LocalClusterType]], *,
        minimum_groups: int = 2) -> Tuple[LocalClusterType, ...]:
    """Learn a shared finite local-type vocabulary across configurations."""
    groups = tuple(tuple(rows) for rows in cluster_types_by_group)
    if (not groups or any(not rows for rows in groups) or
            minimum_groups < 1 or minimum_groups > len(groups)):
        raise ValueError("invalid recurrent prototype groups")
    group_support: Counter[LocalClusterType] = Counter()
    occurrence_support: Counter[LocalClusterType] = Counter()
    colors = set()
    for rows in groups:
        group_support.update(set(rows))
        occurrence_support.update(rows)
        colors.update(row.color_key for row in rows)
    selected = {row for row, support in group_support.items()
                if support >= minimum_groups}
    # Mapping must remain total for every chemistry represented in training.
    for color in colors:
        if any(row.color_key == color for row in selected):
            continue
        candidates = tuple(row for row in group_support
                           if row.color_key == color)
        selected.add(max(candidates, key=lambda row: (
            group_support[row], occurrence_support[row],
            tuple(-value for value in row.cumulative_neighbor_counts), row)))
    return tuple(sorted(selected))


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
        target_colors: Sequence[Hashable] | None = None,
        ) -> RecursiveConnectionMarking:
    """Learn a finite connection marking from one known growth transition."""
    if len(positions) != len(cluster_types) or len(positions) < 2:
        raise ValueError("positions and cluster types must be aligned")
    if scale <= 0 or separation_bin_width <= 0:
        raise ValueError("scale and bin width must be positive")
    target_sequence = tuple(target_positions)
    targets = {point_key(point) for point in target_sequence}
    if target_colors is not None and len(target_colors) != len(target_sequence):
        raise ValueError("target positions and colors must align")
    colors_by_target = ({} if target_colors is None else
                        {point_key(point): repr(color)
                         for point, color in zip(target_sequence, target_colors)})
    counts: Dict[RecursiveConnectionState, list[int]] = defaultdict(
        lambda: [0, 0])
    target_color_evidence: Dict[
        RecursiveConnectionState, Counter[str]] = defaultdict(Counter)
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
            target = point_key(_proposal(parent, source, scale))
            counts[state][1] += 1
            counts[state][0] += target in targets
            if target in colors_by_target:
                target_color_evidence[state][colors_by_target[target]] += 1
    evidence = {state: StateEvidence(positive, total)
                for state, (positive, total) in counts.items()}
    accepted = frozenset(
        state for state, item in evidence.items()
        if item.positive >= minimum_positive_support and
        item.positive / item.total >= minimum_purity)
    return RecursiveConnectionMarking(
        scale, separation_bin_width, tuple(sorted(set(cluster_types))),
        evidence, accepted, minimum_positive_support, minimum_purity,
        dict(target_color_evidence))


def merge_recursive_connection_markings(
        markings: Sequence[RecursiveConnectionMarking], *,
        minimum_positive_support: int = 2,
        minimum_positive_groups: int = 2,
        minimum_purity: float = .5,
        positive_states_by_marking: Sequence[
            Iterable[RecursiveConnectionState]] | None = None,
        ) -> RecursiveConnectionMarking:
    """Merge finite port evidence from independent known configurations.

    States remain exact local cluster-color/separation records. A state is
    admitted only when its pooled evidence is sufficiently pure and it has at
    least one correct connection in the requested number of independent input
    markings. No material label, target outside those training markings, or
    global coordinate enters the merged grammar.
    """
    markings = tuple(markings)
    if (not markings or minimum_positive_support < 1 or
            minimum_positive_groups < 1 or
            not 0. < minimum_purity <= 1.):
        raise ValueError("invalid recursive marking merge")
    scale = markings[0].scale
    width = markings[0].separation_bin_width
    if any(abs(row.scale - scale) > 1e-12 or
           abs(row.separation_bin_width - width) > 1e-12
           for row in markings):
        raise ValueError("recursive markings use incompatible scales or bins")
    if positive_states_by_marking is None:
        positive_rows = tuple(tuple(
            state for state, row in marking.evidence.items()
            if row.positive > 0) for marking in markings)
    else:
        positive_rows = tuple(tuple(rows)
                              for rows in positive_states_by_marking)
        if len(positive_rows) != len(markings):
            raise ValueError("positive-state indices must align with markings")
    positive_groups: Counter[RecursiveConnectionState] = Counter()
    positive_support: Counter[RecursiveConnectionState] = Counter()
    for marking, states in zip(markings, positive_rows):
        for state in states:
            row = marking.evidence.get(state)
            if row is None or row.positive <= 0:
                raise ValueError("positive-state index contains invalid state")
            positive_groups[state] += 1
            positive_support[state] += row.positive
    candidate_states = frozenset(
        state for state, groups in positive_groups.items()
        if groups >= minimum_positive_groups and
        positive_support[state] >= minimum_positive_support)
    counts: Dict[RecursiveConnectionState, list[int]] = {
        state: [0, 0, positive_groups[state]] for state in candidate_states}
    colors: Dict[RecursiveConnectionState, Counter[str]] = defaultdict(Counter)
    for marking in markings:
        for state in candidate_states:
            row = marking.evidence.get(state)
            if row is None:
                continue
            counts[state][0] += row.positive
            counts[state][1] += row.total
            evidence = marking.target_color_evidence.get(state)
            if evidence:
                colors[state].update(evidence)
    evidence = {state: StateEvidence(row[0], row[1])
                for state, row in counts.items()}
    accepted = frozenset(state for state, row in counts.items()
        if row[0] >= minimum_positive_support and
        row[2] >= minimum_positive_groups and
        row[0] / row[1] >= minimum_purity)
    return RecursiveConnectionMarking(
        scale, width, tuple(sorted({prototype for marking in markings
                                    for prototype in marking.prototypes})),
        evidence, accepted, minimum_positive_support, minimum_purity,
        dict(colors))


def propose_with_recursive_marking(
        marking: RecursiveConnectionMarking, positions: Sequence[Point],
        cluster_types: Sequence[LocalClusterType], level_scale: float = 1.0,
        target_positions: Iterable[Point] | None = None,
        parent_indices: Iterable[int] | None = None,
        source_indices: Iterable[int] | None = None,
        ) -> MarkedProposalResult:
    """Apply a frozen marking and aggregate overlapping action proposals."""
    if len(positions) != len(cluster_types) or level_scale <= 0:
        raise ValueError("positions/types must align and level scale be positive")
    mapped = map_to_prototypes(cluster_types, marking.prototypes)
    targets = (None if target_positions is None else
               {point_key(point) for point in target_positions})
    votes: Counter[Point] = Counter()
    color_votes: Dict[Point, Counter[str]] = defaultdict(Counter)
    target_color_votes: Dict[Point, Counter[str]] = defaultdict(Counter)
    state_votes: Dict[Point, Counter[RecursiveConnectionState]] = defaultdict(
        Counter)
    parent_votes: Dict[Point, Counter[int]] = defaultdict(Counter)
    endpoint_votes: Dict[Point, Counter[int]] = defaultdict(Counter)
    accepted_pairs = 0
    true_pairs = 0
    parents = tuple(range(len(positions)) if parent_indices is None
                    else parent_indices)
    if not parents or any(index < 0 or index >= len(positions)
                          for index in parents):
        raise ValueError("parent indices must select known positions")
    sources = tuple(range(len(positions)) if source_indices is None
                    else source_indices)
    if not sources or any(index < 0 or index >= len(positions)
                          for index in sources):
        raise ValueError("source indices must select known positions")
    for parent_index in parents:
        parent = positions[parent_index]
        for source_index in sources:
            source = positions[source_index]
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
            learned_colors = marking.target_color_evidence.get(state)
            predicted_target_color = (min(
                color for color, count in learned_colors.items()
                if count == max(learned_colors.values()))
                if learned_colors else mapped[source_index].color_key)
            target_color_votes[target][predicted_target_color] += 1
            state_votes[target][state] += 1
            parent_votes[target][parent_index] += 1
            endpoint_votes[target][parent_index] += 1
            endpoint_votes[target][source_index] += 1
            if targets is not None:
                true_pairs += target in targets
    return MarkedProposalResult(
        votes, accepted_pairs, None if targets is None else true_pairs,
        dict(color_votes), dict(target_color_votes), dict(state_votes),
        dict(parent_votes), dict(endpoint_votes))


def consensus_sites(votes: Counter[Point], minimum_votes: int) -> frozenset[Point]:
    if minimum_votes < 1:
        raise ValueError("minimum votes must be positive")
    return frozenset(point for point, count in votes.items()
                     if count >= minimum_votes)


def merge_marked_proposal_results(
        results: Iterable[MarkedProposalResult]) -> MarkedProposalResult:
    """Merge independently generated action families by target coordinate."""
    votes: Counter[Point] = Counter()
    colors: Dict[Point, Counter[str]] = defaultdict(Counter)
    target_colors: Dict[Point, Counter[str]] = defaultdict(Counter)
    states: Dict[Point, Counter[RecursiveConnectionState]] = defaultdict(Counter)
    parents: Dict[Point, Counter[int]] = defaultdict(Counter)
    endpoints: Dict[Point, Counter[int]] = defaultdict(Counter)
    accepted_pairs = 0
    true_pairs = 0
    labels_available = True
    for result in results:
        votes.update(result.votes)
        accepted_pairs += result.accepted_pair_actions
        if result.true_pair_actions is None:
            labels_available = False
        else:
            true_pairs += result.true_pair_actions
        for point, evidence in result.color_votes.items():
            colors[point].update(evidence)
        for point, evidence in result.target_color_votes.items():
            target_colors[point].update(evidence)
        for point, evidence in result.state_votes.items():
            states[point].update(evidence)
        for point, evidence in result.parent_votes.items():
            parents[point].update(evidence)
        dependency = (result.causal_endpoint_votes
                      if result.causal_endpoint_votes is not None
                      else result.parent_votes)
        for point, evidence in dependency.items():
            endpoints[point].update(evidence)
    return MarkedProposalResult(
        votes, accepted_pairs, true_pairs if labels_available else None,
        dict(colors), dict(target_colors), dict(states), dict(parents),
        dict(endpoints))
