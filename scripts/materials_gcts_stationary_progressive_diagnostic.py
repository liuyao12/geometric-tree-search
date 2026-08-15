#!/usr/bin/env python3
"""Progressive necessary-field audit for a real promoted hierarchy."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from materials_gcts_macro_stationary_adapter import adapt_macro_type
from materials_gcts_recurring_action_submacro_audit import (
    PromotedSubmacroLevel, _topology_signature)
from materials_gcts_stationary_production_signature import (
    audit_chemical_population_substitution)


@dataclass(frozen=True)
class ProgressiveStationaryDiagnostic:
    consecutive_windows: tuple[tuple[int, int, int], ...]
    child_count_topology_intersections: tuple[int, ...]
    chemistry_chirality_intersections: tuple[int, ...]
    directed_port_semantics_intersections: tuple[int, ...]
    normalized_pose_intersections: tuple[int, ...]
    population_substitution_intersections: tuple[int, ...]
    adapted_candidates: int
    adaptation_rejections: int
    first_zero_field: str | None
    final_stationarity_relaxed: bool


def _semantic_key(production, *, ports):
    count = len(production.children)
    alternatives = []
    for order in itertools.permutations(range(count)):
        mapping = {old: new for new, old in enumerate(order)}
        children = tuple((production.children[old].chemistry_key,
                          production.children[old].chirality_key)
                         for old in order)
        if ports:
            internal = tuple(sorted((
                mapping[item.source], mapping[item.target], item.port_key,
                item.overlap_chemistry)
                for item in production.internal_ports))
            boundary = tuple(sorted((
                mapping[item.child], item.direction,
                item.outside_chemistry_key, item.port_key,
                item.overlap_chemistry)
                for item in production.boundary_slots))
        else:
            internal = tuple(sorted((mapping[item.source],
                                     mapping[item.target])
                                    for item in production.internal_ports))
            boundary = tuple(sorted((mapping[item.child], item.direction)
                                    for item in production.boundary_slots))
        alternatives.append((children, internal, boundary))
    return min(alternatives, key=repr)


def _intersection_counts(key_sets, windows):
    return tuple(len(key_sets[left].intersection(
        key_sets[middle], key_sets[right]))
        for left, middle, right in windows)


def diagnose_progressive_stationarity(
        levels: tuple[PromotedSubmacroLevel, ...], *, tolerance: float = 1e-6,
) -> ProgressiveStationaryDiagnostic:
    by_level = {item.hierarchy_level: item for item in levels}
    windows = tuple((level, level + 1, level + 2)
                    for level in sorted(by_level)
                    if level + 1 in by_level and level + 2 in by_level)
    topology = {level: {_topology_signature(macro)
                        for macro in item.submacros
                        if len(macro.node_types) >= 3}
                for level, item in by_level.items()}
    topology_counts = _intersection_counts(topology, windows)
    eligible = {level: set() for level in by_level}
    for left, middle, right in windows:
        common = topology[left].intersection(topology[middle], topology[right])
        eligible[left].update(common)
        eligible[middle].update(common)
        eligible[right].update(common)

    adapted = {level: [] for level in by_level}
    rejections = 0
    for level, item in by_level.items():
        cache = {}
        for macro in item.submacros:
            if (len(macro.node_types) < 3 or
                    _topology_signature(macro) not in eligible[level]):
                continue
            try:
                adapted[level].append(adapt_macro_type(
                    item.artifact, macro, tolerance=tolerance,
                    prototype_semantics_cache=cache))
            except (KeyError, TypeError, ValueError):
                rejections += 1
    chemistry = {level: {_semantic_key(item.production, ports=False)
                         for item in values}
                 for level, values in adapted.items()}
    ports = {level: {_semantic_key(item.production, ports=True)
                     for item in values}
             for level, values in adapted.items()}
    pose = {level: {item.canonical.normalized_key for item in values}
            for level, values in adapted.items()}
    chemistry_counts = _intersection_counts(chemistry, windows)
    port_counts = _intersection_counts(ports, windows)
    pose_counts = _intersection_counts(pose, windows)

    population_counts = []
    for left, middle, right in windows:
        total = 0
        for key in pose[left].intersection(pose[middle], pose[right]):
            left_items = tuple(item for item in adapted[left]
                               if item.canonical.normalized_key == key)
            middle_items = tuple(item for item in adapted[middle]
                                 if item.canonical.normalized_key == key)
            right_items = tuple(item for item in adapted[right]
                                if item.canonical.normalized_key == key)
            found = False
            for first, second, third in itertools.product(
                    left_items, middle_items, right_items):
                lower = audit_chemical_population_substitution(
                    first.production, second.production)
                upper = audit_chemical_population_substitution(
                    second.production, third.production)
                if (lower.consistent and upper.consistent and
                        lower.substitution_matrix == upper.substitution_matrix):
                    found = True
                    break
            total += int(found)
        population_counts.append(total)
    stages = (
        ("child-count/topology", topology_counts),
        ("reduced-chemistry/chirality", chemistry_counts),
        ("directed-port-semantics", port_counts),
        ("normalized-pose", pose_counts),
        ("population-substitution", tuple(population_counts)))
    first_zero = next((name for name, counts in stages
                       if not counts or not any(counts)), None)
    return ProgressiveStationaryDiagnostic(
        windows, topology_counts, chemistry_counts, port_counts, pose_counts,
        tuple(population_counts), sum(map(len, adapted.values())), rejections,
        first_zero, False)
