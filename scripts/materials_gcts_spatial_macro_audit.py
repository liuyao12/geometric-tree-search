#!/usr/bin/env python3
"""Audit recurrent spatial patches in exact regenerative IQC growth waves.

This deliberately does not promote consecutive time steps.  A candidate macro
must first be a connected colored point patch and recur up to rigid isometry.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Tuple

from materials_gcts_frontier_attachment_benchmark import evaluate as frontier


@dataclass(frozen=True)
class SpatialMacroAudit:
    waves: int
    exact_sites: int
    connection_radius: float
    component_counts_by_wave: Tuple[int, ...]
    component_sizes_by_wave: Tuple[Tuple[int, ...], ...]
    window_width: int
    component_counts_by_window: Tuple[int, ...]
    component_sizes_by_window: Tuple[Tuple[int, ...], ...]
    spatial_patch_occurrences: int
    spatial_patch_types: int
    recurrent_patch_types: int
    recurrent_patch_occurrences: int
    recurrent_multisite_types: int
    largest_recurrent_patch_sites: int
    greatest_wave_span: int
    hierarchy_depth_proved: int
    spatial_recurrence_gate_passed: bool
    exponential_macro_gate_passed: bool
    honest_status: str


def _distance_squared(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right))


def _components(positions, radius):
    neighbors = [[] for _ in positions]
    radius_squared = radius * radius + 1e-10
    for left in range(len(positions)):
        for right in range(left + 1, len(positions)):
            if _distance_squared(positions[left], positions[right]) <= radius_squared:
                neighbors[left].append(right)
                neighbors[right].append(left)
    unseen = set(range(len(positions)))
    result = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        stack = [seed]
        component = []
        while stack:
            index = stack.pop()
            component.append(index)
            for neighbor in neighbors[index]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(component)))
    return tuple(result)


def _patch_signature(positions, species, indices, length_unit):
    """Permutation/translation/rotation invariant colored distance record."""
    colors = tuple(sorted(repr(species[index]) for index in indices))
    pairs = []
    for offset, left in enumerate(indices):
        for right in indices[offset + 1:]:
            color_pair = tuple(sorted((repr(species[left]), repr(species[right]))))
            distance = _distance_squared(positions[left], positions[right]) ** .5
            pairs.append((color_pair, round(distance / length_unit, 5)))
    return len(indices), colors, tuple(sorted(pairs))


def evaluate(waves=16, connection_radius=2.1, window_width=4):
    result = frontier(regenerative_wave_count=waves)
    radius = connection_radius
    signatures = Counter()
    signature_windows = defaultdict(set)
    sizes_by_wave = []
    counts_by_wave = []
    exact_sites = 0
    for trace, wave in zip(result.regenerative_growth_traces,
                           result.regenerative_growth_waves):
        if wave.false_sites:
            raise RuntimeError("spatial macro audit requires exact growth waves")
        exact_sites += len(trace.positions)
        components = _components(trace.positions, radius)
        sizes_by_wave.append(tuple(sorted(
            (len(component) for component in components), reverse=True)))
        counts_by_wave.append(len(components))
    window_counts = []
    window_sizes = []
    traces = result.regenerative_growth_traces
    for start in range(0, len(traces), window_width):
        window = traces[start:start + window_width]
        if len(window) != window_width:
            continue
        positions = tuple(point for trace in window for point in trace.positions)
        species = tuple(color for trace in window for color in trace.species)
        components = _components(positions, radius)
        window_counts.append(len(components))
        window_sizes.append(tuple(sorted(
            (len(component) for component in components), reverse=True)))
        window_id = start // window_width
        for component in components:
            signature = _patch_signature(
                positions, species, component,
                result.learned_minimum_separation)
            signatures[signature] += 1
            signature_windows[signature].add(window_id)

    recurrent = {signature: count for signature, count in signatures.items()
                 if count >= 2}
    recurrent_multisite = {
        signature: count for signature, count in recurrent.items()
        if signature[0] > 1}
    largest = max((signature[0] for signature in recurrent_multisite),
                  default=0)
    greatest_span = max(
        (max(signature_windows[signature]) - min(signature_windows[signature]) + 1
         for signature in recurrent_multisite), default=0)
    recurrence_gate = bool(recurrent_multisite) and greatest_span >= 2
    # A recurrent first-level patch is evidence for one spatial macro level,
    # not yet for a macro made from recurring macros.
    depth = 1 if recurrence_gate else 0
    exponential = depth >= 3
    return SpatialMacroAudit(
        len(result.regenerative_growth_traces), exact_sites, radius,
        tuple(counts_by_wave), tuple(sizes_by_wave), window_width,
        tuple(window_counts), tuple(window_sizes), sum(signatures.values()),
        len(signatures), len(recurrent), sum(recurrent.values()),
        len(recurrent_multisite), largest, greatest_span, depth,
        recurrence_gate, exponential,
        ("recurrent rigid spatial patches found, but no clusters-of-clusters "
         "amplification is yet proved" if recurrence_gate else
         "no recurrent multi-site spatial patch at the declared connection radius"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--waves", type=int, default=16)
    parser.add_argument("--connection-radius", type=float, default=2.1)
    parser.add_argument("--window-width", type=int, default=4)
    arguments = parser.parse_args()
    result = evaluate(
        arguments.waves, arguments.connection_radius, arguments.window_width)
    print(json.dumps(asdict(result), indent=2)
          if arguments.json else result)


if __name__ == "__main__":
    main()
