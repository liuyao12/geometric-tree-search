#!/usr/bin/env python3
"""Order-independent spatial hierarchy gate on an exact IQC frontier."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_frontier_attachment_benchmark import evaluate as frontier
from materials_gcts_spatial_support_hierarchy import (
    guarded_octants, learn_spatial_support_hierarchy,
    nearest_neighbor_scale)


@dataclass(frozen=True)
class SpatialSectorBenchmark:
    exact_frontier_atoms: int
    assigned_atoms: int
    spatial_domains: int
    excluded_guard_atoms: int
    radius_scales: Tuple[float, ...]
    radii: Tuple[float, ...]
    geometry_types: Tuple[int, ...]
    recurrent_types: Tuple[int, ...]
    recurrent_occurrences: Tuple[int, ...]
    largest_recurrent_supports: Tuple[int, ...]
    recurrent_coverages: Tuple[float, ...]
    support_amplification: Tuple[float, ...]
    minimum_support_amplification: float
    hierarchy_depth: int
    exact_cover_each_level: bool
    construction_order_used: bool
    second_level_cluster_of_clusters: bool
    three_level_spatial_hierarchy: bool
    exponential_support_gate_passed: bool
    projected_additional_promotions_to_million: int
    million_projection_verified: bool
    benchmark_passed: bool


def evaluate(waves=16):
    growth = frontier(regenerative_wave_count=waves)
    positions = tuple(point for trace in growth.regenerative_growth_traces
                      for point in trace.positions)
    species = tuple(color for trace in growth.regenerative_growth_traces
                    for color in trace.species)
    if any(wave.false_sites for wave in growth.regenerative_growth_waves):
        raise RuntimeError("spatial sector benchmark requires exact growth")
    scale = nearest_neighbor_scale(positions)
    domains = guarded_octants(positions, margin=.08 * scale)
    radius_scales = (1.08, 2.0, 3.7)
    hierarchy = learn_spatial_support_hierarchy(
        positions, species, domains, radius_scales=radius_scales)
    levels = hierarchy.levels
    supports = tuple(level.largest_recurrent_support for level in levels)
    second = len(levels) >= 2 and supports[1] > supports[0] > 1
    three = hierarchy.hierarchy_depth >= 3
    minimum_amplification = min(hierarchy.support_amplification)
    exponential = three and minimum_amplification > 3.0
    projected = math.ceil(math.log(1_000_000 / supports[-1]) /
                          math.log(minimum_amplification))
    passed = (hierarchy.complete_cover_each_level and
              not hierarchy.construction_order_used and second and
              exponential)
    return SpatialSectorBenchmark(
        len(positions), hierarchy.assigned_atoms, hierarchy.domains,
        len(positions) - hierarchy.assigned_atoms, radius_scales,
        hierarchy.radii,
        tuple(level.geometry_types for level in levels),
        tuple(level.recurrent_types for level in levels),
        tuple(level.recurrent_occurrences for level in levels), supports,
        tuple(level.recurrent_atom_coverage for level in levels),
        hierarchy.support_amplification, minimum_amplification,
        hierarchy.hierarchy_depth,
        hierarchy.complete_cover_each_level,
        hierarchy.construction_order_used, second, three, exponential,
        projected, False, passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--waves", type=int, default=16)
    arguments = parser.parse_args()
    result = evaluate(arguments.waves)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
