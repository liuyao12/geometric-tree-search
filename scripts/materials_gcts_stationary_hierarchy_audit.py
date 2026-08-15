#!/usr/bin/env python3
"""Leakage-safe strong-stationarity audit of the learned IQC hierarchy.

The audit delegates semantics to ``adapt_macro_type``: reduced stoichiometry,
separately audited absolute populations, proper-frame handedness, overlap
chemistry, proper rotation, and intrinsically scaled translation are retained.
Numeric prototype IDs and raw scale-dependent pose keys are not semantics. The
strong canonical production contract removes only admissible world pose,
child ordering/gauge, and one uniform scale.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import itertools

from materials_gcts_irregular_port_atlas import IrregularPortProgram
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_macro_stationary_adapter import adapt_macro_type
from materials_gcts_port_graph_macros import MacroType, mine_port_graph_macros
from materials_gcts_stationary_production_signature import (
    PromotionObservation, stationary_evidence)


@dataclass(frozen=True)
class StrongSemanticLevel:
    level: int
    source_types: int
    positive_mdl_macros: int
    evidence_occurrences: int
    promotion_occurrences: int
    three_child_macros: int
    canonical_productions: int
    canonical_production_keys: tuple[str, ...]
    rejection_reasons: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class StationaryHierarchyAudit:
    levels: tuple[StrongSemanticLevel, ...]
    adjacent_shared_topology_classes: tuple[int, ...]
    adjacent_shared_strong_keys: tuple[int, ...]
    three_consecutive_positive_levels: bool
    strong_stationary_recurrence: bool
    exact_occurrence_expansion_helped: bool
    termination_reason: str
    target_family_cell_expected_scale_unused: bool


def _topology_signature(macro: MacroType) -> tuple:
    count = len(macro.node_types)
    alternatives = []
    import itertools
    for order in itertools.permutations(range(count)):
        mapping = {old: new for new, old in enumerate(order)}
        edges = tuple(sorted((mapping[item.source], mapping[item.target])
                             for item in macro.edges))
        boundary = tuple(sorted((mapping[item.node], item.direction)
                                for item in macro.boundary_slots))
        alternatives.append((count, edges, boundary))
    return min(alternatives)


def _has_strong_stationary_recurrence(adapted_levels, positive) -> bool:
    """Require one key and equal learned scales across three levels."""
    if not any(all(positive[index:index + 3])
               for index in range(max(0, len(positive) - 2))):
        return False
    for index in range(max(0, len(adapted_levels) - 2)):
        if not all(positive[index:index + 3]):
            continue
        common = set(adapted_levels[index]).intersection(
            adapted_levels[index + 1], adapted_levels[index + 2])
        for key in common:
            for observations in itertools.product(
                    adapted_levels[index][key],
                    adapted_levels[index + 1][key],
                    adapted_levels[index + 2][key]):
                if stationary_evidence(observations).stationary:
                    return True
    return False


def audit_stationary_hierarchy(
    initial: IrregularPortProgram, *, maximum_nodes: int = 3,
    maximum_levels: int = 8,
) -> StationaryHierarchyAudit:
    artifact = initial
    raw_levels = []
    expansion_helped = False
    termination = "level_limit"
    for level in range(maximum_levels):
        mined = mine_port_graph_macros(artifact, maximum_nodes=maximum_nodes)
        macros = mined.macro_types
        evidence_count = sum(len(item.occurrences) for item in macros)
        promotion_count = sum(len(item.promotion_occurrences or
                                  item.occurrences) for item in macros)
        expansion_helped |= promotion_count > evidence_count
        topology = {_topology_signature(item) for item in macros
                    if len(item.node_types) >= 3}
        raw_levels.append((artifact, macros, evidence_count, promotion_count,
                           topology))
        if not macros:
            termination = "no_positive_mdl"
            break
        artifact = promote_macro_types(
            artifact, macros, level=level + 1)
    topology_sets = tuple(item[4] for item in raw_levels)
    shared_topology = tuple(len(left.intersection(right))
                            for left, right in zip(topology_sets,
                                                  topology_sets[1:]))
    reports = []
    adapted_levels = []
    strong_sets = []
    for level, (level_artifact, macros, evidence_count, promotion_count,
                topology) in enumerate(raw_levels):
        semantics_cache = {}
        adjacent_topologies = set()
        if level:
            adjacent_topologies.update(topology.intersection(
                topology_sets[level - 1]))
        if level + 1 < len(topology_sets):
            adjacent_topologies.update(topology.intersection(
                topology_sets[level + 1]))
        adapted_by_key = {}
        reasons = Counter()
        skipped = 0
        for macro in macros:
            if len(macro.node_types) < 3:
                continue
            if _topology_signature(macro) not in adjacent_topologies:
                skipped += 1
                continue
            try:
                adapted = adapt_macro_type(
                    level_artifact, macro,
                    prototype_semantics_cache=semantics_cache)
                if not adapted.leakage_clean:
                    raise ValueError("stationary adapter leakage audit failed")
                observation = PromotionObservation(
                    level, adapted.production, len(macro.occurrences),
                    macro.maximum_occurrence_atom_overlap_fraction,
                    macro.mdl_saving, True)
                adapted_by_key.setdefault(
                    adapted.canonical.normalized_key, []).append(observation)
            except (KeyError, ValueError) as error:
                reasons[str(error)] += 1
        if skipped:
            reasons["topology absent from adjacent level"] += skipped
        strong = set(adapted_by_key)
        strong_sets.append(strong)
        adapted_levels.append(adapted_by_key)
        reports.append(StrongSemanticLevel(
            level, len(level_artifact.prototypes), len(macros), evidence_count,
            promotion_count, sum(len(item.node_types) >= 3 for item in macros),
            sum(len(value) for value in adapted_by_key.values()),
            tuple(sorted(strong)), tuple(sorted(reasons.items()))))
    shared_strong = tuple(len(left.intersection(right))
                          for left, right in zip(strong_sets, strong_sets[1:]))
    positive = tuple(report.positive_mdl_macros > 0 for report in reports)
    three_positive = any(all(positive[index:index + 3])
                         for index in range(max(0, len(positive) - 2)))
    strong_stationary = _has_strong_stationary_recurrence(
        adapted_levels, positive)
    return StationaryHierarchyAudit(
        tuple(reports), shared_topology, shared_strong, three_positive,
        strong_stationary, expansion_helped, termination, True)
