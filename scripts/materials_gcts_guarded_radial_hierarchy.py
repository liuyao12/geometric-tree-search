#!/usr/bin/env python3
"""Frozen local cluster hierarchy with cumulative radial train/test guards."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Hashable, Sequence, Tuple

from materials_gcts_frozen_hierarchy import (
    Signature, _SpatialIndex, _all_signatures, _species_key, _training_scale)


def _bounded_color(signature: Signature) -> Signature:
    """Backoff color: bounded coordination and angular histograms."""
    _, body, angular = signature
    coordination = Counter(label for label, _ in body)
    angles = Counter(cosine_bin for _, _, cosine_bin in angular)
    return tuple(sorted(coordination.items())), tuple(sorted(angles.items()))


@dataclass
class GuardedRadialLevel:
    level: int
    radius: float
    dependency_radius: float
    training_centers: int
    known_signatures: int
    recurring_signatures: int
    unknown_label: int
    backoff_radius: int
    _known: frozenset[Signature] = field(repr=False)
    _lookup: dict[Signature, int] = field(repr=False)
    _assignment_cache: dict[Signature, int] = field(
        default_factory=dict, repr=False)


@dataclass
class GuardedRadialEncoder:
    length_unit: float
    species_labels: dict[str, int]
    levels: Tuple[GuardedRadialLevel, ...]
    training_radius: float


@dataclass(frozen=True)
class GuardedRadialReplayLevel:
    level: int
    dependency_radius: float
    training_centers: int
    heldout_centers: int
    known_heldout_fraction: float
    promoted_heldout_fraction: float
    frozen_signatures: int
    promoted_signatures: int
    median_nearest_color_distance: float
    p95_nearest_color_distance: float
    raw_domains_disjoint: bool


def _radius(point):
    return math.sqrt(sum(value * value for value in point))


def _color_distance(left: Signature, right: Signature) -> int:
    result = 0
    for left_items, right_items in zip(left, right):
        left_counts, right_counts = dict(left_items), dict(right_items)
        result += sum(abs(left_counts.get(key, 0) - right_counts.get(key, 0))
                      for key in set(left_counts) | set(right_counts))
    return result


def _assign(signature: Signature, level: GuardedRadialLevel) -> int:
    cached = level._assignment_cache.get(signature)
    if cached is not None:
        return cached
    exact = level._lookup.get(signature)
    if exact is not None:
        level._assignment_cache[signature] = exact
        return exact
    candidate = min(
        ((_color_distance(signature, known), label)
         for known, label in level._lookup.items()), default=None)
    if candidate is not None and candidate[0] <= level.backoff_radius:
        assigned = candidate[1]
    else:
        assigned = level.unknown_label
    level._assignment_cache[signature] = assigned
    return assigned


def _nearest_distance(signature: Signature, level: GuardedRadialLevel) -> int:
    if signature in level._lookup:
        return 0
    return min((_color_distance(signature, known)
                for known in level._lookup), default=10 ** 9)


def _weighted_quantile(values, fraction):
    total = sum(weight for _, weight in values)
    target = fraction * total
    cumulative = 0
    for value, weight in sorted(values):
        cumulative += weight
        if cumulative >= target:
            return float(value)
    return 0.0


def fit_guarded_radial_hierarchy(
    configuration,
    training_radius: float,
    *,
    maximum_levels: int = 3,
    radius_growth: float = 1.85,
    first_radius_scale: float = 1.08,
    minimum_occurrences: int = 2,
) -> GuardedRadialEncoder:
    points = configuration.positions
    first_candidates = tuple(index for index, point in enumerate(points)
                             if _radius(point) <= training_radius * .5)
    scale = _training_scale(points, first_candidates)
    species_keys = tuple(_species_key(value) for value in configuration.species)
    ordered = sorted(set(species_keys))
    species_map = {chemical: index for index, chemical in enumerate(ordered)}
    labels = tuple(species_map[value] for value in species_keys)
    spatial = _SpatialIndex(points, scale)
    levels = []
    dependency = 0.0
    for offset in range(maximum_levels):
        radius = scale * first_radius_scale * radius_growth ** offset
        dependency += radius
        centers = tuple(index for index, point in enumerate(points)
                        if _radius(point) <= training_radius - dependency - 1e-9)
        if not centers:
            raise ValueError(f"no guarded training centers at level {offset + 1}")
        # These are bounded GCTS colors, not atomically exact identities.
        # Coarse first-level bins let nearby acceptance-window states share a
        # transferable color; exact geometry remains in the production replay.
        descriptor = scale * .20
        angle = .08
        signatures = tuple(_bounded_color(signature) for signature in
                           _all_signatures(points, labels, spatial, radius,
                                           descriptor, angle))
        counts = Counter(signatures[index] for index in centers)
        recurring = tuple(sorted(
            (signature for signature, count in counts.items()
             if count >= minimum_occurrences), key=repr))
        lookup = {signature: label for label, signature in enumerate(recurring)}
        unknown = len(lookup)
        nearest = []
        for signature in recurring:
            distances = [_color_distance(signature, other)
                         for other in recurring if other != signature]
            if distances:
                nearest.append(min(distances))
        # The bounded halo is fixed from training colors. Recursive label drift
        # compounds at level three, where two training widths are admitted.
        # Lower levels retain one width to reject disordered local geometry.
        backoff = (2 if offset >= 2 else 1) * max(nearest, default=0)
        levels.append(GuardedRadialLevel(
            offset + 1, radius, dependency, len(centers), len(counts),
            len(recurring), unknown, backoff, frozenset(counts), lookup))
        labels = tuple(_assign(signature, levels[-1])
                       for signature in signatures)
    return GuardedRadialEncoder(
        scale, species_map, tuple(levels), training_radius)


def replay_guarded_radial_hierarchy(
    configuration,
    encoder: GuardedRadialEncoder,
    evaluation_radius: float,
) -> Tuple[GuardedRadialReplayLevel, ...]:
    points = configuration.positions
    species_keys = tuple(_species_key(value) for value in configuration.species)
    unknown_species = len(encoder.species_labels)
    labels = tuple(encoder.species_labels.get(value, unknown_species)
                   for value in species_keys)
    spatial = _SpatialIndex(points, encoder.length_unit)
    reports = []
    for offset, level in enumerate(encoder.levels):
        descriptor = encoder.length_unit * .20
        angle = .08
        signatures = tuple(_bounded_color(signature) for signature in
                           _all_signatures(points, labels, spatial,
                                           level.radius, descriptor, angle))
        centers = tuple(index for index, point in enumerate(points)
                        if (encoder.training_radius + level.dependency_radius + 1e-9 <=
                            _radius(point) <=
                            evaluation_radius - level.dependency_radius - 1e-9))
        known = sum(signatures[index] in level._known for index in centers)
        assigned = tuple(_assign(signature, level) for signature in signatures)
        promoted = sum(assigned[index] != level.unknown_label
                       for index in centers)
        center_signatures = Counter(signatures[index] for index in centers)
        distances = [(_nearest_distance(signature, level), count)
                     for signature, count in center_signatures.items()]
        reports.append(GuardedRadialReplayLevel(
            level.level, level.dependency_radius, level.training_centers,
            len(centers), known / max(1, len(centers)),
            promoted / max(1, len(centers)), level.known_signatures,
            level.recurring_signatures,
            _weighted_quantile(distances, .5),
            _weighted_quantile(distances, .95), True))
        labels = assigned
    return tuple(reports)
