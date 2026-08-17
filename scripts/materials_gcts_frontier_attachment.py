#!/usr/bin/env python3
"""GCTS marking for attaching recursive proposals to an accepted frontier.

The descriptor combines a proposal's clusters-of-clusters evidence with the
bounded colored geometry it sees in the configuration already accepted by the
search.  It is a geometric connection section, not a physical energy.  All
features are invariant under a common rigid motion.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Hashable, Iterable, List, Sequence, Tuple

from materials_gcts_recursive_connections import MarkedProposalResult, Point, point_key

Descriptor = Tuple[float, ...]


@dataclass(frozen=True)
class FrontierAttachmentMarker:
    radial_edges: Tuple[float, ...]
    color_keys: Tuple[str, ...]
    means: Descriptor
    scales: Descriptor
    weights: Descriptor
    bias: float
    training_examples: int
    training_positives: int


@dataclass(frozen=True)
class FrontierAttachmentExample:
    proposals: MarkedProposalResult
    known_positions: Tuple[Point, ...]
    known_colors: Tuple[Hashable, ...]
    target_positions: Tuple[Point, ...]


def _nearby_cells(key: Tuple[int, int, int]):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                yield key[0] + dx, key[1] + dy, key[2] + dz


def describe_frontier_attachments(
        proposals: MarkedProposalResult, known_positions: Sequence[Point],
        known_colors: Sequence[Hashable], radial_edges: Sequence[float],
        color_keys: Sequence[str] | None = None) -> Dict[Point, Descriptor]:
    if len(known_positions) != len(known_colors) or not known_positions:
        raise ValueError("known positions and colors must be nonempty and aligned")
    edges = tuple(float(edge) for edge in radial_edges)
    if not proposals.votes or not edges or any(
            left >= right for left, right in zip(edges, edges[1:])):
        raise ValueError("proposals must be nonempty and edges strictly increase")
    colors = tuple(color_keys or sorted({repr(color) for color in known_colors}))
    cell = edges[-1]
    grid: Dict[Tuple[int, int, int], List[Tuple[Point, str]]] = defaultdict(list)
    for position, color in zip(known_positions, known_colors):
        key = tuple(math.floor(value / cell) for value in position)
        grid[key].append((position, repr(color)))
    result = {}
    for candidate in sorted(proposals.votes):
        key = tuple(math.floor(value / cell) for value in candidate)
        neighbors = []
        for nearby in _nearby_cells(key):
            for position, color in grid.get(nearby, ()):
                separation = math.dist(candidate, position)
                if separation <= edges[-1]:
                    neighbors.append((separation, color))
        separations = sorted(separation for separation, _ in neighbors)
        vote_count = proposals.votes[candidate]
        source_colors = proposals.color_votes[candidate]
        target_colors = proposals.target_color_votes[candidate]
        descriptor = [
            min(separations, default=edges[-1] + 1.0),
            math.log1p(vote_count),
            max(source_colors.values(), default=0) / vote_count,
            max(target_colors.values(), default=0) / vote_count,
        ]
        descriptor.extend(math.log1p(sum(distance <= edge
                                         for distance in separations))
                          for edge in edges)
        for color in colors:
            descriptor.extend(math.log1p(sum(
                distance <= edge and neighbor_color == color
                for distance, neighbor_color in neighbors))
                for edge in edges)
        descriptor.extend((separations + [edges[-1] + 1.0] * 6)[:6])
        result[candidate] = tuple(descriptor)
    return result


def _sigmoid(value: float) -> float:
    if value >= 0:
        inverse = math.exp(-min(value, 40.0))
        return 1.0 / (1.0 + inverse)
    exponential = math.exp(max(value, -40.0))
    return exponential / (1.0 + exponential)


def _fit_frontier_rows(rows, labels, radial_edges, color_keys, epochs,
                       learning_rate, regularization):
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise ValueError("frontier training requires both classes")
    dimensions = len(rows[0])
    means = tuple(sum(row[axis] for row in rows) / len(rows)
                  for axis in range(dimensions))
    scales = tuple(max(1e-6, (sum((row[axis] - means[axis]) ** 2
                                  for row in rows) / len(rows)) ** .5)
                   for axis in range(dimensions))
    normalized = tuple(tuple(max(-8., min(8.,
        (row[axis] - means[axis]) / scales[axis]))
        for axis in range(dimensions)) for row in rows)
    weights = [0.0] * dimensions
    bias = 0.0
    positive_weight = .5 / positives
    negative_weight = .5 / negatives
    for epoch in range(epochs):
        gradient = [regularization * weight for weight in weights]
        bias_gradient = 0.0
        for row, label in zip(normalized, labels):
            prediction = _sigmoid(
                bias + sum(weight * value
                           for weight, value in zip(weights, row)))
            sample_weight = positive_weight if label else negative_weight
            error = sample_weight * (prediction - label)
            bias_gradient += error
            for axis, value in enumerate(row):
                gradient[axis] += error * value
        step = learning_rate / math.sqrt(1.0 + epoch / 40.0)
        weights = [weight - step * gradient_value
                   for weight, gradient_value in zip(weights, gradient)]
        bias -= step * bias_gradient
    return FrontierAttachmentMarker(
        tuple(radial_edges), color_keys, means, scales, tuple(weights), bias,
        len(rows), positives)


def fit_frontier_attachment_marker_examples(
        examples: Sequence[FrontierAttachmentExample],
        radial_edges: Sequence[float] = (1.4, 2.1, 2.8, 3.81),
        epochs: int = 500, learning_rate: float = .4,
        regularization: float = .01) -> FrontierAttachmentMarker:
    """Fit one rigid-motion-invariant marking over several configurations."""
    if not examples:
        raise ValueError("frontier training requires at least one example")
    color_keys = tuple(sorted({repr(color) for example in examples
                               for color in example.known_colors}))
    rows = []
    labels = []
    for example in examples:
        described = describe_frontier_attachments(
            example.proposals, example.known_positions,
            example.known_colors, radial_edges, color_keys)
        targets = {point_key(point) for point in example.target_positions}
        for point in sorted(described):
            rows.append(described[point])
            labels.append(int(point_key(point) in targets))
    return _fit_frontier_rows(
        tuple(rows), tuple(labels), radial_edges, color_keys, epochs,
        learning_rate, regularization)


def fit_frontier_attachment_marker(
        proposals: MarkedProposalResult, known_positions: Sequence[Point],
        known_colors: Sequence[Hashable], target_positions: Iterable[Point],
        radial_edges: Sequence[float] = (1.4, 2.1, 2.8, 3.81),
        epochs: int = 500, learning_rate: float = .4,
        regularization: float = .01) -> FrontierAttachmentMarker:
    example = FrontierAttachmentExample(
        proposals, tuple(known_positions), tuple(known_colors),
        tuple(target_positions))
    return fit_frontier_attachment_marker_examples(
        (example,), radial_edges, epochs, learning_rate, regularization)


def score_frontier_attachments(
        marker: FrontierAttachmentMarker, proposals: MarkedProposalResult,
        known_positions: Sequence[Point], known_colors: Sequence[Hashable],
        ) -> Dict[Point, float]:
    described = describe_frontier_attachments(
        proposals, known_positions, known_colors,
        marker.radial_edges, marker.color_keys)
    result = {}
    for point, row in described.items():
        normalized = tuple(max(-8., min(8.,
            (row[axis] - marker.means[axis]) / marker.scales[axis]))
            for axis in range(len(row)))
        result[point] = _sigmoid(
            marker.bias + sum(weight * value for weight, value
                              in zip(marker.weights, normalized)))
    return result
