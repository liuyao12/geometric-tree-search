#!/usr/bin/env python3
"""Incremental compatibility of tentative sites with recurrent clusters.

The score is purely geometric and chemical.  It asks how much inserting a
bounded colored point set changes the nearest-prototype residual of affected
existing clusters, and how well the inserted sites themselves match the
frozen recurrent vocabulary.  No target sites, lattice coordinates, material
family, or physical potential enter the calculation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable, Sequence

from materials_gcts_recursive_connections import (
    LocalClusterType, Point, local_cluster_types)


@dataclass(frozen=True)
class PrototypeCompatibilityContext:
    positions: tuple[Point, ...]
    encoded_colors: tuple[str, ...]
    radial_edges: tuple[float, ...]
    color_keys: tuple[str, ...]
    baseline_types: tuple[LocalClusterType, ...]
    prototypes: tuple[LocalClusterType, ...]
    baseline_residuals: tuple[int, ...]


@dataclass(frozen=True)
class PrototypeInsertionCompatibility:
    inserted_residuals: tuple[int, ...]
    affected_existing_atoms: int
    existing_residual_delta: int
    total_residual_delta: int
    local_maximum_residual: int
    target_used: bool = False


def _residual(cluster_type, prototypes):
    candidates = tuple(row for row in prototypes
                       if row.color_key == cluster_type.color_key)
    if not candidates:
        raise ValueError(f"no prototype for color {cluster_type.color_key}")
    return min(sum(abs(left - right) for left, right in zip(
        cluster_type.cumulative_neighbor_counts,
        prototype.cumulative_neighbor_counts)) for prototype in candidates)


def fit_prototype_compatibility_context(
        positions: Sequence[Point], colors: Sequence[Hashable],
        radial_edges: Sequence[float],
        prototypes: Sequence[LocalClusterType],
        ) -> PrototypeCompatibilityContext:
    positions = tuple(tuple(map(float, point)) for point in positions)
    encoded = tuple(repr(color) for color in colors)
    edges = tuple(map(float, radial_edges))
    prototypes = tuple(sorted(set(prototypes)))
    if (not positions or len(positions) != len(encoded) or not prototypes or
            not edges or edges[0] <= 0 or any(left >= right
                             for left, right in zip(edges, edges[1:]))):
        raise ValueError("invalid prototype compatibility context")
    color_keys = tuple(sorted(set(encoded)))
    if any(not any(row.color_key == color for row in prototypes)
           for color in color_keys):
        raise ValueError("prototype vocabulary does not cover every color")
    baseline = local_cluster_types(positions, colors, edges)
    residuals = tuple(_residual(row, prototypes) for row in baseline)
    return PrototypeCompatibilityContext(
        positions, encoded, edges, color_keys, baseline, prototypes,
        residuals)


def score_prototype_insertions(
        context: PrototypeCompatibilityContext,
        inserted_positions: Sequence[Point],
        inserted_colors: Sequence[Hashable],
        ) -> PrototypeInsertionCompatibility:
    inserted = tuple(tuple(map(float, point))
                     for point in inserted_positions)
    encoded = tuple(repr(color) for color in inserted_colors)
    if (not inserted or len(inserted) != len(encoded) or
            len(set(inserted)) != len(inserted) or
            any(color not in context.color_keys for color in encoded) or
            any(math.dist(point, known) <= 1e-12
                for point in inserted for known in context.positions)):
        raise ValueError("invalid inserted colored sites")
    maximum = context.radial_edges[-1]
    width = len(context.radial_edges)
    offsets = {color: index * width
               for index, color in enumerate(context.color_keys)}
    affected = 0
    existing_delta = 0
    local_residuals = []
    for index, (position, cluster_type) in enumerate(zip(
            context.positions, context.baseline_types)):
        counts = list(cluster_type.cumulative_neighbor_counts)
        changed = False
        for point, color in zip(inserted, encoded):
            distance = math.dist(position, point)
            if distance > maximum:
                continue
            offset = offsets[color]
            for edge_index, edge in enumerate(context.radial_edges):
                counts[offset + edge_index] += distance <= edge
            changed = True
        if not changed:
            continue
        updated = LocalClusterType(cluster_type.color_key, tuple(counts))
        residual = _residual(updated, context.prototypes)
        existing_delta += residual - context.baseline_residuals[index]
        local_residuals.append(residual)
        affected += 1

    inserted_residuals = []
    for index, (center, center_color) in enumerate(zip(inserted, encoded)):
        counts = {color: [0] * width for color in context.color_keys}
        neighbors = tuple(zip(context.positions, context.encoded_colors)) + \
            tuple((point, color) for other, (point, color) in enumerate(
                  zip(inserted, encoded)) if other != index)
        for point, color in neighbors:
            distance = math.dist(center, point)
            if distance > maximum:
                continue
            for edge_index, edge in enumerate(context.radial_edges):
                counts[color][edge_index] += distance <= edge
        row = LocalClusterType(center_color, tuple(
            value for color in context.color_keys for value in counts[color]))
        residual = _residual(row, context.prototypes)
        inserted_residuals.append(residual)
        local_residuals.append(residual)
    total_delta = existing_delta + sum(inserted_residuals)
    return PrototypeInsertionCompatibility(
        tuple(inserted_residuals), affected, existing_delta, total_delta,
        max(local_residuals, default=0))
