#!/usr/bin/env python3
"""Second-order GCTS sections on neighborhoods of overlapping proposals.

The first recursive marking produces a covering: multiple parent/source
connections can propose the same site.  This module promotes the bounded
neighborhood of those votes to another cluster type and learns a scalar marking
on it.  Descriptors use only vote multiplicities and radial distances between
proposals, so they are invariant under a common rigid motion and contain no
oracle coordinates, lattice axes, or physical energies.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from bisect import bisect_right
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from materials_gcts_recursive_connections import (
    Point, RecursiveConnectionState, point_key)

Descriptor = Tuple[float, ...]


@dataclass(frozen=True)
class ConsensusNeighborhoodMarker:
    radial_edges: Tuple[float, ...]
    means: Descriptor
    scales: Descriptor
    weights: Descriptor
    bias: float
    training_examples: int
    training_positives: int


@dataclass(frozen=True)
class BinnedConsensusNeighborhoodMarker:
    radial_edges: Tuple[float, ...]
    feature_edges: Tuple[Tuple[float, ...], ...]
    bin_log_odds: Tuple[Tuple[float, ...], ...]
    training_examples: int
    training_positives: int


def _cells_near(key: Tuple[int, int, int], reach: int):
    for dx in range(-reach, reach + 1):
        for dy in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                yield key[0] + dx, key[1] + dy, key[2] + dz


def describe_consensus_neighborhoods(
        votes: Counter[Point], radial_edges: Sequence[float],
        color_votes: Mapping[Point, Counter[str]] | None = None,
        state_votes: Mapping[Point, Counter[RecursiveConnectionState]] | None = None,
        ) -> Dict[Point, Descriptor]:
    """Describe each proposal by its vote and nearby proposal-vote cluster."""
    edges = tuple(float(edge) for edge in radial_edges)
    if not votes or not edges or any(
            left >= right for left, right in zip(edges, edges[1:])):
        raise ValueError("votes must be nonempty and edges strictly increasing")
    cell = edges[-1]
    points = tuple(sorted(votes))
    grid: Dict[Tuple[int, int, int], List[Point]] = defaultdict(list)
    for point in points:
        grid[tuple(math.floor(value / cell) for value in point)].append(point)
    maximum_vote = max(votes.values())
    descriptors = {}
    for point in points:
        key = tuple(math.floor(value / cell) for value in point)
        neighbor_records = []
        for neighboring_cell in _cells_near(key, 1):
            for other in grid.get(neighboring_cell, ()):
                if other == point:
                    continue
                separation = math.dist(point, other)
                if separation <= edges[-1]:
                    neighbor_records.append((separation, votes[other]))
        own_vote = votes[point]
        local_maximum = max((vote for _, vote in neighbor_records),
                            default=own_vote)
        descriptor = [
            math.log1p(own_vote),
            own_vote / maximum_vote,
            own_vote / max(own_vote, local_maximum),
        ]
        colors = (color_votes or {}).get(point, Counter())
        states = (state_votes or {}).get(point, Counter())
        parent_types = {state.parent_type for state in states}
        source_types = {state.source_type for state in states}
        descriptor.extend((
            max(colors.values(), default=0) / own_vote,
            math.log1p(len(colors)),
            max(states.values(), default=0) / own_vote,
            math.log1p(len(states)),
            math.log1p(len(parent_types)),
            math.log1p(len(source_types)),
        ))
        for edge in edges:
            local = [vote for separation, vote in neighbor_records
                     if separation <= edge]
            descriptor.extend((
                math.log1p(len(local)),
                math.log1p(sum(local)),
                sum(vote >= 2 for vote in local) / max(1, len(local)),
                sum(vote >= 4 for vote in local) / max(1, len(local)),
            ))
        descriptors[point] = tuple(descriptor)
    return descriptors


def _sigmoid(value: float) -> float:
    if value >= 0:
        inverse = math.exp(-min(value, 40.0))
        return 1.0 / (1.0 + inverse)
    exponential = math.exp(max(value, -40.0))
    return exponential / (1.0 + exponential)


def _normalize_descriptor_set(descriptors: Sequence[Descriptor]):
    dimensions = len(descriptors[0])
    means = tuple(sum(row[axis] for row in descriptors) / len(descriptors)
                  for axis in range(dimensions))
    scales = tuple(max(1e-6, (sum((row[axis] - means[axis]) ** 2
                                  for row in descriptors) /
                              len(descriptors)) ** .5)
                   for axis in range(dimensions))
    normalized = tuple(tuple(max(-8., min(8.,
        (row[axis] - means[axis]) / scales[axis]))
        for axis in range(dimensions)) for row in descriptors)
    return means, scales, normalized


def fit_consensus_neighborhood_marker(
        votes: Counter[Point], target_positions: Iterable[Point],
        radial_edges: Sequence[float] = (.8, 1.4, 2.1, 2.8, 3.81),
        epochs: int = 350, learning_rate: float = .35,
        regularization: float = .01,
        color_votes: Mapping[Point, Counter[str]] | None = None,
        state_votes: Mapping[Point, Counter[RecursiveConnectionState]] | None = None,
        ) -> ConsensusNeighborhoodMarker:
    """Fit a class-balanced logistic section on one labelled transition."""
    descriptors_by_point = describe_consensus_neighborhoods(
        votes, radial_edges, color_votes, state_votes)
    points = tuple(sorted(descriptors_by_point))
    descriptors = tuple(descriptors_by_point[point] for point in points)
    targets = {point_key(point) for point in target_positions}
    labels = tuple(int(point in targets) for point in points)
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise ValueError("second-order training requires both classes")
    dimensions = len(descriptors[0])
    means, scales, normalized = _normalize_descriptor_set(descriptors)
    weights = [0.0] * dimensions
    bias = 0.0
    positive_weight = .5 / positives
    negative_weight = .5 / negatives
    for epoch in range(epochs):
        gradient = [regularization * value for value in weights]
        bias_gradient = 0.0
        for row, label in zip(normalized, labels):
            score = _sigmoid(bias + sum(weight * value
                                       for weight, value in zip(weights, row)))
            sample_weight = positive_weight if label else negative_weight
            error = sample_weight * (score - label)
            bias_gradient += error
            for axis, value in enumerate(row):
                gradient[axis] += error * value
        step = learning_rate / math.sqrt(1.0 + epoch / 40.0)
        weights = [weight - step * value
                   for weight, value in zip(weights, gradient)]
        bias -= step * bias_gradient
    return ConsensusNeighborhoodMarker(
        tuple(radial_edges), means, scales, tuple(weights), bias,
        len(labels), positives)


def score_consensus_neighborhoods(
        marker: ConsensusNeighborhoodMarker, votes: Counter[Point],
        color_votes: Mapping[Point, Counter[str]] | None = None,
        state_votes: Mapping[Point, Counter[RecursiveConnectionState]] | None = None,
        ) -> Dict[Point, float]:
    descriptors = describe_consensus_neighborhoods(
        votes, marker.radial_edges, color_votes, state_votes)
    result = {}
    for point, descriptor in descriptors.items():
        normalized = tuple(max(-8., min(8.,
            (descriptor[axis] - marker.means[axis]) / marker.scales[axis]))
            for axis in range(len(descriptor)))
        result[point] = _sigmoid(
            marker.bias + sum(weight * value for weight, value
                              in zip(marker.weights, normalized)))
    return result


def fit_binned_consensus_neighborhood_marker(
        votes: Counter[Point], target_positions: Iterable[Point],
        radial_edges: Sequence[float] = (.8, 1.4, 2.1, 2.8, 3.81),
        bins: int = 12, smoothing: float = 2.0,
        color_votes: Mapping[Point, Counter[str]] | None = None,
        state_votes: Mapping[Point, Counter[RecursiveConnectionState]] | None = None,
        ) -> BinnedConsensusNeighborhoodMarker:
    """Fit an interpretable finite section of per-feature likelihood bins."""
    if bins < 2 or smoothing <= 0:
        raise ValueError("at least two bins and positive smoothing required")
    described = describe_consensus_neighborhoods(
        votes, radial_edges, color_votes, state_votes)
    points = tuple(sorted(described))
    rows = tuple(described[point] for point in points)
    targets = {point_key(point) for point in target_positions}
    labels = tuple(int(point in targets) for point in points)
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise ValueError("second-order training requires both classes")
    all_edges = []
    all_log_odds = []
    for axis in range(len(rows[0])):
        ordered = sorted(row[axis] for row in rows)
        edges = tuple(sorted(set(
            ordered[min(len(ordered) - 1, round(len(ordered) * q / bins))]
            for q in range(1, bins))))
        positive_counts = [0] * (len(edges) + 1)
        negative_counts = [0] * (len(edges) + 1)
        for row, label in zip(rows, labels):
            index = bisect_right(edges, row[axis])
            (positive_counts if label else negative_counts)[index] += 1
        bin_count = len(edges) + 1
        positive_denominator = positives + smoothing * bin_count
        negative_denominator = negatives + smoothing * bin_count
        odds = tuple(math.log(
            ((positive + smoothing) / positive_denominator) /
            ((negative + smoothing) / negative_denominator))
            for positive, negative in zip(positive_counts, negative_counts))
        all_edges.append(edges)
        all_log_odds.append(odds)
    return BinnedConsensusNeighborhoodMarker(
        tuple(radial_edges), tuple(all_edges), tuple(all_log_odds),
        len(labels), positives)


def score_binned_consensus_neighborhoods(
        marker: BinnedConsensusNeighborhoodMarker, votes: Counter[Point],
        color_votes: Mapping[Point, Counter[str]] | None = None,
        state_votes: Mapping[Point, Counter[RecursiveConnectionState]] | None = None,
        ) -> Dict[Point, float]:
    described = describe_consensus_neighborhoods(
        votes, marker.radial_edges, color_votes, state_votes)
    result = {}
    normalization = math.sqrt(len(marker.feature_edges))
    for point, row in described.items():
        logit = sum(odds[bisect_right(edges, value)]
                    for value, edges, odds in zip(
                        row, marker.feature_edges, marker.bin_log_odds))
        result[point] = _sigmoid(logit / normalization)
    return result
