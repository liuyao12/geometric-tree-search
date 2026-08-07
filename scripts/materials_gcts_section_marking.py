#!/usr/bin/env python3
"""Material-generic bounded GCTS sections for proposed cluster actions.

The module knows nothing about Sc, Zn, crystals, quasicrystals, lattices, or
physical potentials.  It receives a colored point cloud, independently learned
cluster centres, and proposed ``(parent, source)`` pairs.  Two finite sections
describe the atomic decoration around the source relative to the intrinsic
parent-to-source axis:

* radial/axial occupancy bins;
* continuous even Legendre moments.

Both are invariant under a common rigid motion.  A GCTS marking is the
conjunction of their independently fitted k-nearest-section decisions.  The
output is a filter for tree-search actions, not an energy model.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Hashable, Iterable, List, Sequence, Tuple

Point = Tuple[float, float, float]
Descriptor = Tuple[float, ...]


@dataclass(frozen=True)
class ColoredPoint:
    position: Point
    colors: Tuple[Hashable, ...]


@dataclass(frozen=True)
class MarkingExample:
    parent: int
    source: int
    accepted: int = 0
    group: Hashable = 0
    target: Point | None = None


@dataclass(frozen=True)
class SectionSettings:
    neighbors: int
    threshold: float


@dataclass(frozen=True)
class NormalizedKnnSection:
    settings: SectionSettings
    means: Descriptor
    scales: Descriptor
    training_vectors: Tuple[Descriptor, ...]
    training_labels: Tuple[int, ...]


@dataclass(frozen=True)
class GctsSectionMarker:
    radius: float
    radial_edges: Tuple[float, ...]
    chemical: bool
    histogram: NormalizedKnnSection
    moments: NormalizedKnnSection
    descriptor_dimensions: int


@dataclass(frozen=True)
class MarkingPrediction:
    example: MarkingExample
    histogram_score: float
    moment_score: float
    accepted: bool


def distance(left: Point, right: Point) -> float:
    return math.dist(left, right)


def _neighbor_cells(key: Tuple[int, int, int]):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                yield key[0] + dx, key[1] + dy, key[2] + dz


def _spatial_index(points: Sequence[Point], cell: float):
    grid: Dict[Tuple[int, int, int], List[int]] = defaultdict(list)
    for index, point in enumerate(points):
        grid[tuple(math.floor(value / cell) for value in point)].append(index)
    return grid


def _legendre(order: int, value: float) -> float:
    previous, current = 1.0, value
    if order == 0:
        return previous
    if order == 1:
        return current
    for degree in range(2, order + 1):
        previous, current = current, (
            ((2 * degree - 1) * value * current -
             (degree - 1) * previous) / degree)
    return current


def _local_environments(
        points: Sequence[ColoredPoint], centers: Sequence[Point], radius: float,
        sources: Iterable[int]):
    positions = [point.position for point in points]
    grid = _spatial_index(positions, radius)
    environments = {}
    for source in set(sources):
        center = centers[source]
        key = tuple(math.floor(value / radius) for value in center)
        records = []
        for neighbor in _neighbor_cells(key):
            for point_index in grid.get(neighbor, ()):
                point = points[point_index]
                vector = tuple(point.position[axis] - center[axis]
                               for axis in range(3))
                radial = math.sqrt(sum(value * value for value in vector))
                if 0.0 < radial <= radius:
                    records.append((vector, radial, point.colors))
        environments[source] = tuple(records)
    return environments


def describe_examples(
        points: Sequence[ColoredPoint], centers: Sequence[Point],
        examples: Sequence[MarkingExample], radius: float,
        radial_edges: Sequence[float] | None = None, chemical: bool = False,
        moment_orders: Sequence[int] = (2, 4, 6, 8),
        axial_bins: int = 4) -> Tuple[Tuple[Descriptor, ...],
                                     Tuple[Descriptor, ...]]:
    """Return histogram and moment sections in example order."""
    if radius <= 0:
        raise ValueError("section radius must be positive")
    edges = tuple(radial_edges or (.45 * radius, .70 * radius, radius))
    if not edges or edges[-1] != radius or any(
            left >= right for left, right in zip((0.0,) + edges, edges)):
        raise ValueError("radial edges must increase and terminate at radius")
    colors = sorted({color for point in points for color in point.colors},
                    key=lambda value: (type(value).__qualname__, repr(value)))
    channels: Tuple[Hashable | None, ...] = tuple(colors) if chemical else (None,)
    environments = _local_environments(
        points, centers, radius, (example.source for example in examples))
    histograms = []
    moments = []
    for example in examples:
        parent = centers[example.parent]
        source = centers[example.source]
        axis = tuple(source[coordinate] - parent[coordinate]
                     for coordinate in range(3))
        pair_distance = math.sqrt(sum(value * value for value in axis))
        if pair_distance <= 1e-12:
            raise ValueError("parent and source must be distinct")
        unit = tuple(value / pair_distance for value in axis)
        histogram = [0] * (len(edges) * len(channels) * axial_bins)
        moment = [pair_distance]
        records = environments[example.source]
        for radial_index, (low, high) in enumerate(
                zip((0.0,) + edges[:-1], edges)):
            for channel_index, channel in enumerate(channels):
                cosines = []
                for vector, radial, point_colors in records:
                    if not low < radial <= high:
                        continue
                    if channel is not None and channel not in point_colors:
                        continue
                    cosine = sum(vector[coordinate] * unit[coordinate]
                                 for coordinate in range(3)) / radial
                    cosines.append(cosine)
                    axial = min(axial_bins - 1, max(
                        0, int((cosine + 1.0) * axial_bins / 2.0)))
                    offset = ((radial_index * len(channels) + channel_index) *
                              axial_bins + axial)
                    histogram[offset] += 1
                moment.append(float(len(cosines)))
                moment.extend(sum(_legendre(order, cosine)
                                  for cosine in cosines)
                              for order in moment_orders)
        histograms.append((pair_distance,) + tuple(histogram))
        moments.append(tuple(moment))
    return tuple(histograms), tuple(moments)


def _fit_knn(descriptors: Sequence[Descriptor], labels: Sequence[int],
             settings: SectionSettings) -> NormalizedKnnSection:
    if not descriptors or len(descriptors) != len(labels):
        raise ValueError("descriptors and labels must be nonempty and aligned")
    dimensions = len(descriptors[0])
    if any(len(descriptor) != dimensions for descriptor in descriptors):
        raise ValueError("descriptor dimensions differ")
    if not 1 <= settings.neighbors <= len(descriptors):
        raise ValueError("invalid neighbor count")
    means = tuple(sum(row[axis] for row in descriptors) / len(descriptors)
                  for axis in range(dimensions))
    scales = tuple(max(1e-6, (sum((row[axis] - means[axis]) ** 2
                                  for row in descriptors) /
                              len(descriptors)) ** .5)
                   for axis in range(dimensions))
    vectors = tuple(tuple((row[axis] - means[axis]) / scales[axis]
                          for axis in range(dimensions))
                    for row in descriptors)
    return NormalizedKnnSection(
        settings, means, scales, vectors, tuple(int(label) for label in labels))


def _knn_score(model: NormalizedKnnSection, descriptor: Descriptor) -> float:
    vector = tuple((descriptor[axis] - model.means[axis]) / model.scales[axis]
                   for axis in range(len(descriptor)))
    nearest: List[Tuple[float, int]] = []
    for known, label in zip(model.training_vectors, model.training_labels):
        separation = sum((left - right) ** 2
                         for left, right in zip(known, vector))
        if len(nearest) < model.settings.neighbors:
            nearest.append((separation, label))
            nearest.sort()
        elif separation < nearest[-1][0]:
            nearest[-1] = separation, label
            nearest.sort()
    weights = [1.0 / (math.sqrt(separation) + 1e-6)
               for separation, _ in nearest]
    return sum(weight * label for weight, (_, label)
               in zip(weights, nearest)) / sum(weights)


def select_settings(
        descriptors: Sequence[Descriptor], examples: Sequence[MarkingExample],
        neighbor_options: Sequence[int] = (1, 3, 5, 7),
        thresholds: Sequence[float] = (.35, .45, .50, .55, .65, .75, .85)
        ) -> SectionSettings:
    """Choose a section rule by grouped cross-validation.

    Every example sharing a parent/group is held out together, preventing
    nearly identical actions around one parent from appearing on both sides of
    a validation fold.  When the caller supplies only one group, leave-one-
    example-out folds are used as the minimal fallback.
    """
    if len(descriptors) != len(examples) or not examples:
        raise ValueError("descriptors and examples must be nonempty and aligned")
    labels = [int(example.accepted) for example in examples]
    if len(set(labels)) == 1:
        return SectionSettings(1, .5)
    group_values = [example.group for example in examples]
    groups = list(dict.fromkeys(group_values))
    fold_ids = (group_values if len(groups) > 1 else
                list(range(len(examples))))
    folds = list(dict.fromkeys(fold_ids))
    valid_neighbors = [neighbors for neighbors in neighbor_options
                       if all(neighbors <= len(examples) -
                              sum(fold == candidate for candidate in fold_ids)
                              for fold in folds)]
    if not valid_neighbors:
        raise ValueError("not enough cross-group examples for requested neighbors")
    scores = {neighbors: [0.0] * len(examples)
              for neighbors in valid_neighbors}
    for fold in folds:
        training_indices = [index for index, candidate in enumerate(fold_ids)
                            if candidate != fold]
        validation_indices = [index for index, candidate in enumerate(fold_ids)
                              if candidate == fold]
        training_descriptors = [descriptors[index]
                                for index in training_indices]
        training_labels = [labels[index] for index in training_indices]
        base = _fit_knn(
            training_descriptors, training_labels,
            SectionSettings(max(valid_neighbors), .5))
        for neighbors in valid_neighbors:
            model = NormalizedKnnSection(
                SectionSettings(neighbors, .5), base.means, base.scales,
                base.training_vectors, base.training_labels)
            for index in validation_indices:
                scores[neighbors][index] = _knn_score(
                    model, descriptors[index])
    positives = sum(labels)
    negatives = len(labels) - positives
    choices = []
    for neighbors in valid_neighbors:
        for threshold in thresholds:
            predictions = [score >= threshold for score in scores[neighbors]]
            true_positive = sum(prediction and label
                                for prediction, label in zip(predictions, labels))
            true_negative = sum(not prediction and not label
                                for prediction, label in zip(predictions, labels))
            balanced = .5 * (true_positive / positives +
                             true_negative / negatives)
            predicted = sum(predictions)
            precision = true_positive / predicted if predicted else 0.0
            # Precision and a conservative threshold break equal-accuracy ties;
            # smaller neighborhoods win only after those causal metrics tie.
            choices.append((balanced, precision, threshold, -neighbors,
                            SectionSettings(neighbors, threshold)))
    return max(choices)[-1]


def fit_marker(
        points: Sequence[ColoredPoint], centers: Sequence[Point],
        examples: Sequence[MarkingExample], radius: float,
        histogram_settings: SectionSettings,
        moment_settings: SectionSettings,
        radial_edges: Sequence[float] | None = None,
        chemical: bool = False) -> GctsSectionMarker:
    histograms, moments = describe_examples(
        points, centers, examples, radius, radial_edges, chemical)
    labels = [example.accepted for example in examples]
    histogram = _fit_knn(histograms, labels, histogram_settings)
    moment = _fit_knn(moments, labels, moment_settings)
    return GctsSectionMarker(
        radius, tuple(radial_edges or (.45 * radius, .70 * radius, radius)),
        chemical, histogram, moment,
        len(histograms[0]) + len(moments[0]))


def fit_marker_auto(
        points: Sequence[ColoredPoint], centers: Sequence[Point],
        examples: Sequence[MarkingExample], radius: float,
        radial_edges: Sequence[float] | None = None,
        chemical: bool = False) -> GctsSectionMarker:
    """Fit both section settings by parent-group cross-validation."""
    histograms, moments = describe_examples(
        points, centers, examples, radius, radial_edges, chemical)
    histogram_settings = select_settings(histograms, examples)
    moment_settings = select_settings(moments, examples)
    labels = [example.accepted for example in examples]
    histogram = _fit_knn(histograms, labels, histogram_settings)
    moment = _fit_knn(moments, labels, moment_settings)
    return GctsSectionMarker(
        radius, tuple(radial_edges or (.45 * radius, .70 * radius, radius)),
        chemical, histogram, moment,
        len(histograms[0]) + len(moments[0]))


def predict(
        marker: GctsSectionMarker, points: Sequence[ColoredPoint],
        centers: Sequence[Point], examples: Sequence[MarkingExample]
        ) -> Tuple[MarkingPrediction, ...]:
    histograms, moments = describe_examples(
        points, centers, examples, marker.radius, marker.radial_edges,
        marker.chemical)
    predictions = []
    for example, histogram, moment in zip(examples, histograms, moments):
        histogram_score = _knn_score(marker.histogram, histogram)
        moment_score = _knn_score(marker.moments, moment)
        accepted = (histogram_score >= marker.histogram.settings.threshold and
                    moment_score >= marker.moments.settings.threshold)
        predictions.append(MarkingPrediction(
            example, histogram_score, moment_score, accepted))
    return tuple(predictions)


def transform_rigid(point: Point, rotation: Sequence[Sequence[float]],
                    translation: Point) -> Point:
    return tuple(sum(rotation[row][column] * point[column]
                     for column in range(3)) + translation[row]
                 for row in range(3))
