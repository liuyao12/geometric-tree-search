#!/usr/bin/env python3
"""Frozen production alternatives for cumulative-guarded GCTS colors."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence, Tuple

from materials_gcts_frozen_hierarchy import (
    _SpatialIndex, _all_signatures, _species_key)
from materials_gcts_guarded_radial_hierarchy import (
    GuardedRadialEncoder, _assign, _bounded_color, _radius)


ProductionFingerprint = Tuple[object, ...]


@dataclass(frozen=True)
class FrozenProductionLevel:
    level: int
    sampled_training_parents: int
    parent_colors: int
    production_alternatives: int
    maximum_alternatives_per_color: int
    median_alternatives_per_color: float
    recurring_alternatives: int


@dataclass(frozen=True)
class FrozenProductionAtlas:
    levels: Tuple[FrozenProductionLevel, ...]
    alternatives: Tuple[Tuple[Tuple[int, Tuple[ProductionFingerprint, ...]], ...], ...]
    sample_limit_per_level: int
    geometry_uses_heldout_atoms: bool


@dataclass(frozen=True)
class ProductionReplayLevel:
    level: int
    sampled_heldout_parents: int
    parents_with_known_color: int
    exact_production_matches: int
    known_color_fraction: float
    exact_production_fraction: float
    exact_given_known_color: float
    unseen_production_fingerprints: int


def _quantize(value, unit):
    return round(value / max(1e-12, unit * 1e-5))


def _production_fingerprint(points, labels, support, center, unit):
    """Colored distance-graph fingerprint, centered on a distinguished site."""
    center_point = points[center]
    rows = []
    for index in support:
        radial = _quantize(math.dist(center_point, points[index]), unit)
        distances = tuple(sorted(
            (labels[other], _quantize(math.dist(points[index], points[other]), unit))
            for other in support if other != index))
        rows.append((labels[index], radial, distances))
    return labels[center], tuple(sorted(rows))


def _sample(indices, limit):
    if len(indices) <= limit:
        return tuple(indices)
    step = len(indices) / limit
    return tuple(indices[min(len(indices) - 1, int(offset * step))]
                 for offset in range(limit))


def _level_labels(configuration, encoder):
    points = configuration.positions
    species_keys = tuple(_species_key(value) for value in configuration.species)
    unknown_species = len(encoder.species_labels)
    labels = tuple(encoder.species_labels.get(value, unknown_species)
                   for value in species_keys)
    spatial = _SpatialIndex(points, encoder.length_unit)
    results = []
    for level in encoder.levels:
        raw = _all_signatures(
            points, labels, spatial, level.radius,
            encoder.length_unit * .20, .08)
        colors = tuple(_bounded_color(signature) for signature in raw)
        assigned = tuple(_assign(color, level) for color in colors)
        results.append((labels, assigned, spatial))
        labels = assigned
    return tuple(results)


def fit_frozen_production_atlas(
    configuration,
    encoder: GuardedRadialEncoder,
    *,
    sample_limit_per_level: int = 4096,
) -> FrozenProductionAtlas:
    points = configuration.positions
    encoded = _level_labels(configuration, encoder)
    summaries = []
    frozen = []
    for level, (child_labels, parent_labels, spatial) in zip(
            encoder.levels, encoded):
        eligible = tuple(index for index, point in enumerate(points)
                         if _radius(point) <=
                         encoder.training_radius - level.dependency_radius - 1e-9)
        sampled = _sample(eligible, sample_limit_per_level)
        grouped = defaultdict(Counter)
        for center in sampled:
            support = tuple(index for _, index in
                            spatial.within(center, level.radius))
            fingerprint = _production_fingerprint(
                points, child_labels, support, center, encoder.length_unit)
            grouped[parent_labels[center]][fingerprint] += 1
        alternatives = tuple(sorted(
            (color, tuple(sorted(counts, key=repr)))
            for color, counts in grouped.items()))
        counts = sorted(len(items) for _, items in alternatives)
        recurring = sum(sum(value >= 2 for value in grouped[color].values())
                        for color, _ in alternatives)
        median = (counts[len(counts) // 2] if len(counts) % 2 else
                  (counts[len(counts) // 2 - 1] + counts[len(counts) // 2]) / 2)
        summaries.append(FrozenProductionLevel(
            level.level, len(sampled), len(alternatives), sum(counts),
            max(counts), median, recurring))
        frozen.append(alternatives)
    return FrozenProductionAtlas(
        tuple(summaries), tuple(frozen), sample_limit_per_level, False)


def replay_frozen_production_atlas(
    configuration,
    encoder: GuardedRadialEncoder,
    atlas: FrozenProductionAtlas,
    evaluation_radius: float,
) -> Tuple[ProductionReplayLevel, ...]:
    points = configuration.positions
    encoded = _level_labels(configuration, encoder)
    reports = []
    for level, frozen, (child_labels, parent_labels, spatial) in zip(
            encoder.levels, atlas.alternatives, encoded):
        eligible = tuple(index for index, point in enumerate(points)
                         if (encoder.training_radius + level.dependency_radius + 1e-9 <=
                             _radius(point) <=
                             evaluation_radius - level.dependency_radius - 1e-9))
        sampled = _sample(eligible, atlas.sample_limit_per_level)
        alternatives = {color: set(items) for color, items in frozen}
        known = matches = 0
        unseen = set()
        for center in sampled:
            color = parent_labels[center]
            choices = alternatives.get(color)
            if choices is None:
                continue
            known += 1
            support = tuple(index for _, index in
                            spatial.within(center, level.radius))
            fingerprint = _production_fingerprint(
                points, child_labels, support, center, encoder.length_unit)
            if fingerprint in choices:
                matches += 1
            else:
                unseen.add((color, fingerprint))
        reports.append(ProductionReplayLevel(
            level.level, len(sampled), known, matches,
            known / max(1, len(sampled)), matches / max(1, len(sampled)),
            matches / max(1, known), len(unseen)))
    return tuple(reports)
