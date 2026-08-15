#!/usr/bin/env python3
"""Strict stationarity audit for recursively promoted action submacros.

The audit consumes only learned promoted levels.  It deliberately has no
material-family, unit-cell, target, golden-ratio, or prescribed-scale input.
Each real macro is first resolved through the atlas-to-production semantic
adapter, then compared with the existing chemistry/chirality/population-aware
stationary signature.

Three consecutive levels are required: seeing a patch twice is only a
similarity observation, not evidence for a stationary recursive production.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from materials_gcts_macro_stationary_adapter import (
    AdaptedMacroProduction, adapt_macro_type)
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, PromotionObservation, StationaryProductionEvidence,
    canonicalize_production, stationary_evidence)


@dataclass(frozen=True)
class PromotedSubmacroLevel:
    """One train-only hierarchy level and its admitted positive-MDL macros."""

    hierarchy_level: int
    artifact: Any
    submacros: tuple[Any, ...]


@dataclass(frozen=True)
class ActionSubmacroRecord:
    """Semantic production plus the spatial evidence that admitted it."""

    hierarchy_level: int
    record_id: str
    production: PortGraphProduction
    occurrence_supports: tuple[frozenset[int], ...]
    mdl_saving: int
    learned_from_training_only: bool = True
    leakage_clean: bool = True


@dataclass(frozen=True)
class RejectedSubmacro:
    hierarchy_level: int
    record_id: str
    reason: str


@dataclass(frozen=True)
class StationarySubmacroWitness:
    record_ids: tuple[str, str, str]
    evidence: StationaryProductionEvidence
    independent_occurrences: tuple[int, int, int]
    maximum_selected_overlap_fractions: tuple[float, float, float]


@dataclass(frozen=True)
class RecurringActionSubmacroAudit:
    stationary: bool
    input_levels: tuple[int, ...]
    adapted_records: int
    eligible_records: int
    common_normalized_keys: int
    evaluated_consecutive_triples: int
    witnesses: tuple[StationarySubmacroWitness, ...]
    rejected: tuple[RejectedSubmacro, ...]
    leakage_clean: bool
    reason: str


def _topology_signature(macro: Any) -> tuple:
    """Cheap necessary invariant before expensive prototype semantics."""
    count = len(macro.node_types)
    alternatives = []
    for order in itertools.permutations(range(count)):
        mapping = {old: new for new, old in enumerate(order)}
        edges = tuple(sorted((mapping[item.source], mapping[item.target])
                             for item in macro.edges))
        boundary = tuple(sorted((mapping[item.node], item.direction)
                                for item in macro.boundary_slots))
        alternatives.append((count, edges, boundary))
    return min(alternatives)


def _overlap_fraction(left: frozenset[int], right: frozenset[int]) -> float:
    denominator = min(len(left), len(right))
    return 1.0 if denominator == 0 else len(left & right) / denominator


def _independent_subset(
        supports: Sequence[frozenset[int]], maximum_overlap: float,
) -> tuple[tuple[frozenset[int], ...], float]:
    """Return a deterministic conservative spatially independent subset.

    Trying every possible start removes the most obvious greedy-order
    dependence without making admission exponential in the number of learned
    embeddings.  Under-counting can only reject evidence; it cannot create a
    false stationary certificate.
    """
    unique = tuple(sorted(set(supports), key=lambda item: (
        len(item), tuple(sorted(item)))))
    candidates = []
    for start in range(len(unique)):
        chosen = [unique[start]]
        for support in unique:
            if support == unique[start]:
                continue
            if all(_overlap_fraction(support, old) <= maximum_overlap
                   for old in chosen):
                chosen.append(support)
        candidates.append(tuple(chosen))
    if not candidates:
        return (), 1.0
    chosen = max(candidates, key=lambda items: (
        len(items), tuple(tuple(sorted(item)) for item in items)))
    pairwise = tuple(_overlap_fraction(left, right)
                     for index, left in enumerate(chosen)
                     for right in chosen[index + 1:])
    return chosen, max(pairwise, default=0.0)


def adapt_promoted_submacro_levels(
        levels: Sequence[PromotedSubmacroLevel], *, tolerance: float = 1e-6,
        adapter: Callable[..., AdaptedMacroProduction] = adapt_macro_type,
) -> tuple[tuple[ActionSubmacroRecord, ...], tuple[RejectedSubmacro, ...]]:
    """Resolve real atlas macros without consuming material metadata.

    One prototype-semantics cache is shared across all macros at a level, so
    large promoted prototypes are canonicalized once rather than per macro.
    """
    records = []
    rejected = []
    topology_by_level = {
        level.hierarchy_level: {
            _topology_signature(macro) for macro in level.submacros
            if len(macro.node_types) >= 3}
        for level in levels}
    eligible_topology_by_level = {level.hierarchy_level: set()
                                  for level in levels}
    ordered_levels = sorted(topology_by_level)
    for hierarchy_level in ordered_levels:
        if (hierarchy_level + 1 not in topology_by_level or
                hierarchy_level + 2 not in topology_by_level):
            continue
        common = (topology_by_level[hierarchy_level].intersection(
            topology_by_level[hierarchy_level + 1],
            topology_by_level[hierarchy_level + 2]))
        for offset in range(3):
            eligible_topology_by_level[hierarchy_level + offset].update(common)
    for level in sorted(levels, key=lambda item: item.hierarchy_level):
        semantics_cache = {}
        for ordinal, macro in enumerate(level.submacros):
            macro_id = getattr(macro, "macro_id", ordinal)
            record_id = f"L{level.hierarchy_level}:M{macro_id}"
            if len(macro.node_types) < 3:
                rejected.append(RejectedSubmacro(
                    level.hierarchy_level, record_id,
                    "stationary production needs at least three children"))
                continue
            if (_topology_signature(macro) not in
                    eligible_topology_by_level[level.hierarchy_level]):
                rejected.append(RejectedSubmacro(
                    level.hierarchy_level, record_id,
                    "topology absent from every consecutive three-level intersection"))
                continue
            try:
                adapted = adapter(
                    level.artifact, macro, tolerance=tolerance,
                    prototype_semantics_cache=semantics_cache)
            except (KeyError, TypeError, ValueError) as error:
                rejected.append(RejectedSubmacro(
                    level.hierarchy_level, record_id, str(error)))
                continue
            occurrences = (getattr(macro, "occurrences", ()) or
                           getattr(macro, "promotion_occurrences", ()))
            supports = tuple(frozenset(item.atom_indices)
                             for item in occurrences)
            records.append(ActionSubmacroRecord(
                level.hierarchy_level, record_id, adapted.production,
                supports, int(getattr(macro, "mdl_saving", 0)),
                bool(getattr(level.artifact,
                             "learned_from_training_only", True)),
                adapted.leakage_clean))
    return tuple(records), tuple(rejected)


def audit_action_submacro_records(
        records: Sequence[ActionSubmacroRecord], *, tolerance: float = 1e-6,
        maximum_evidence_overlap_fraction: float = .1,
) -> RecurringActionSubmacroAudit:
    """Find a common strict production across three consecutive levels."""
    if tolerance <= 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    if not 0 <= maximum_evidence_overlap_fraction < 1:
        raise ValueError("maximum evidence overlap must be in [0, 1)")
    rejected = []
    grouped: dict[str, dict[int, list[tuple[
        ActionSubmacroRecord, PromotionObservation, int, float]]]] = {}
    leakage_clean = True
    levels = tuple(sorted({item.hierarchy_level for item in records}))
    eligible = 0
    for record in records:
        leakage_clean = (leakage_clean and record.leakage_clean and
                         record.learned_from_training_only)
        try:
            canonical = canonicalize_production(
                record.production, tolerance=tolerance)
        except ValueError as error:
            rejected.append(RejectedSubmacro(
                record.hierarchy_level, record.record_id, str(error)))
            continue
        selected, overlap = _independent_subset(
            record.occurrence_supports, maximum_evidence_overlap_fraction)
        observation = PromotionObservation(
            record.hierarchy_level, record.production, len(selected), overlap,
            record.mdl_saving,
            record.learned_from_training_only and record.leakage_clean)
        if (len(selected) < 2 or overlap > maximum_evidence_overlap_fraction or
                record.mdl_saving <= 0 or
                not observation.learned_from_training_only):
            reasons = []
            if len(selected) < 2:
                reasons.append("fewer than two independent spatial occurrences")
            if record.mdl_saving <= 0:
                reasons.append("nonpositive MDL saving")
            if not observation.learned_from_training_only:
                reasons.append("not leakage-clean train evidence")
            rejected.append(RejectedSubmacro(
                record.hierarchy_level, record.record_id, "; ".join(reasons)))
            continue
        eligible += 1
        grouped.setdefault(canonical.normalized_key, {}).setdefault(
            record.hierarchy_level, []).append(
                (record, observation, len(selected), overlap))

    common_keys = 0
    evaluated = 0
    witnesses = []
    for by_level in grouped.values():
        ordered_levels = sorted(by_level)
        has_consecutive = any((level + 1 in by_level and level + 2 in by_level)
                              for level in ordered_levels)
        common_keys += int(has_consecutive)
        for level in ordered_levels:
            if level + 1 not in by_level or level + 2 not in by_level:
                continue
            for triple in itertools.product(
                    by_level[level], by_level[level + 1], by_level[level + 2]):
                evaluated += 1
                evidence = stationary_evidence(
                    tuple(item[1] for item in triple), tolerance=tolerance,
                    maximum_evidence_overlap_fraction=
                    maximum_evidence_overlap_fraction)
                if evidence.stationary:
                    witnesses.append(StationarySubmacroWitness(
                        tuple(item[0].record_id for item in triple), evidence,
                        tuple(item[2] for item in triple),
                        tuple(item[3] for item in triple)))
    witnesses.sort(key=lambda item: item.record_ids)
    stationary = bool(witnesses)
    reason = "" if stationary else (
        "no common normalized production passed equal adjacent learned scales, "
        "equal substitution matrices, independent recurrence, and positive MDL "
        "across three consecutive train levels")
    return RecurringActionSubmacroAudit(
        stationary, levels, len(records), eligible, common_keys, evaluated,
        tuple(witnesses), tuple(rejected), leakage_clean, reason)


def audit_promoted_submacro_levels(
        levels: Sequence[PromotedSubmacroLevel], *, tolerance: float = 1e-6,
        maximum_evidence_overlap_fraction: float = .1,
        adapter: Callable[..., AdaptedMacroProduction] = adapt_macro_type,
) -> RecurringActionSubmacroAudit:
    """Adapt and audit real recursively promoted macro levels."""
    records, adaptation_rejections = adapt_promoted_submacro_levels(
        levels, tolerance=tolerance, adapter=adapter)
    result = audit_action_submacro_records(
        records, tolerance=tolerance,
        maximum_evidence_overlap_fraction=maximum_evidence_overlap_fraction)
    return RecurringActionSubmacroAudit(
        result.stationary, result.input_levels, result.adapted_records,
        result.eligible_records, result.common_normalized_keys,
        result.evaluated_consecutive_triples, result.witnesses,
        adaptation_rejections + result.rejected, result.leakage_clean,
        result.reason)


def mine_and_audit_promoted_submacros(
        initial_artifact: Any, *, maximum_levels: int = 3,
        maximum_nodes: int = 3, tolerance: float = 1e-6,
        miner: Callable[..., Any] | None = None,
        quotient: Callable[..., Any] | None = None,
        promoter: Callable[..., Any] | None = None,
) -> RecurringActionSubmacroAudit:
    """Run the available generic miner/promotion API, then audit it honestly.

    The callbacks make the benchmark injectable.  With defaults this is the
    real port-graph macro miner, exact-support quotient, and macro promoter.
    Failure to reach three positive-MDL promoted levels returns a red audit;
    the driver never manufactures missing scales or production children.
    """
    if maximum_levels < 1:
        raise ValueError("maximum_levels must be positive")
    if maximum_nodes < 3:
        raise ValueError("maximum_nodes must permit a connected production")
    if miner is None:
        from materials_gcts_port_graph_macros import mine_port_graph_macros
        miner = mine_port_graph_macros
    if quotient is None:
        from materials_gcts_promoted_type_quotient import quotient_macro_supports
        quotient = quotient_macro_supports
    if promoter is None:
        from materials_gcts_macro_promotion import promote_macro_types
        promoter = promote_macro_types

    artifact = initial_artifact
    levels = []
    for level in range(maximum_levels):
        mined = miner(artifact, maximum_nodes=maximum_nodes)
        admitted = tuple(item for item in mined.macro_types
                         if item.mdl_saving > 0)
        quotiented = quotient(admitted)
        macros = tuple(quotiented.quotient_macros)
        levels.append(PromotedSubmacroLevel(level, artifact, macros))
        if not macros or level + 1 == maximum_levels:
            break
        artifact = promoter(artifact, macros, level=level + 1)
    return audit_promoted_submacro_levels(levels, tolerance=tolerance)
