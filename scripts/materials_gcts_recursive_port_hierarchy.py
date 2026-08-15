#!/usr/bin/env python3
"""Injectable recursive driver for positive-MDL port-graph macros.

The driver itself knows no lattice scale, material family, phase label, unit
cell, or expected growth constant.  A level miner returns finite macro
summaries and a promoter optionally constructs the next artifact.  Iteration
ends only when the miner returns no positive-MDL macros, promotion is currently
unavailable, or an explicit safety limit is reached.

Adjacent levels produce diagnostic normalized structural signatures. A
stationary witness is emitted only when the supplying adapter explicitly marks
its signature as certified by the chemistry/chirality-preserving stationary
production contract. Raw atlas pose-key normalization alone is never promoted
to stationary evidence.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

from materials_gcts_port_graph_macros import MacroType, mine_port_graph_macros

ProductionSignature = tuple[Any, ...]


@dataclass(frozen=True)
class HierarchyMacroSummary:
    atom_support: int
    child_support: int
    mdl_saving: int
    production_signature: ProductionSignature
    stationarity_certified: bool = False


@dataclass(frozen=True)
class MinedHierarchyLevel:
    source_type_count: int
    macros: tuple[HierarchyMacroSummary, ...]
    promotion_payload: Any = None


@dataclass(frozen=True)
class HierarchyLevelRecord:
    level: int
    source_type_count: int
    positive_macro_types: int
    atom_supports: tuple[int, ...]
    child_supports: tuple[int, ...]
    production_type_count: int
    production_signatures: tuple[ProductionSignature, ...]
    certified_stationarity_signatures: tuple[ProductionSignature, ...]
    total_mdl_saving: int


@dataclass(frozen=True)
class StationaryProductionWitness:
    lower_level: int
    upper_level: int
    production_signature: ProductionSignature


@dataclass(frozen=True)
class RecursivePortHierarchy:
    levels: tuple[HierarchyLevelRecord, ...]
    stationary_witnesses: tuple[StationaryProductionWitness, ...]
    termination_reason: str
    converged_no_positive_mdl: bool
    promotion_available: bool
    maximum_levels: int
    stationary_witnesses_require_certified_semantics: bool
    material_family_cell_scale_constants_unused: bool


MineCallback = Callable[[Any, int], MinedHierarchyLevel]
PromoteCallback = Callable[
    [Any, MinedHierarchyLevel, int], Optional[Any]]


@dataclass(frozen=True)
class HierarchyCallbacks:
    mine: MineCallback
    promote: PromoteCallback


def _alpha_normalize_types(values: Sequence[int]) -> tuple[tuple[int, ...], dict[int, int]]:
    mapping: dict[int, int] = {}
    normalized = []
    for value in values:
        if value not in mapping:
            mapping[value] = len(mapping)
        normalized.append(mapping[value])
    return tuple(normalized), mapping


def normalized_macro_signature(macro: MacroType) -> ProductionSignature:
    """Remove arbitrary type IDs, node order, world frame, and uniform scale."""
    pose_keys = [tuple(edge.port[2]) for edge in macro.edges]
    pose_keys.extend(tuple(slot.port[2]) for slot in macro.boundary_slots)
    translation_lengths = [math.sqrt(sum(value*value for value in key[-3:]))
                           for key in pose_keys if len(key) >= 12]
    scale = min((value for value in translation_lengths if value > 0),
                default=1.0)

    def normalized_pose(key: Sequence[int]) -> tuple[int, ...]:
        key = tuple(key)
        if len(key) < 12:
            return key
        return key[:-3] + tuple(round(value / scale * 1_000_000)
                                for value in key[-3:])

    alternatives = []
    node_count = len(macro.node_types)
    for order in itertools.permutations(range(node_count)):
        new_index = {old: new for new, old in enumerate(order)}
        ordered_types = tuple(macro.node_types[old] for old in order)
        type_partition, _ = _alpha_normalize_types(ordered_types)
        edges = tuple(sorted(
            (new_index[edge.source], new_index[edge.target],
             normalized_pose(edge.port[2]))
            for edge in macro.edges))
        # Encode each outside type by its complete boundary incidence, not its
        # arbitrary integer identifier. Internal-type equality is retained by
        # its alpha-normalized node classes.
        incidences: dict[int, list[tuple]] = {}
        for slot in macro.boundary_slots:
            incidences.setdefault(slot.outside_type, []).append((
                new_index[slot.node], slot.direction,
                normalized_pose(slot.port[2])))
        internal_class = {
            raw_type: type_partition[index]
            for index, raw_type in enumerate(ordered_types)}
        outside_descriptors = {
            raw_type: (internal_class.get(raw_type, -1),
                       tuple(sorted(values, key=repr)))
            for raw_type, values in incidences.items()}
        boundary = tuple(sorted([
            (new_index[slot.node], slot.direction,
             outside_descriptors[slot.outside_type],
             normalized_pose(slot.port[2]))
            for slot in macro.boundary_slots], key=repr))
        alternatives.append((type_partition, edges, boundary))
    structure = min(alternatives, key=repr)
    return ("finite_oriented_port_substitution",) + structure


def summarize_port_macro(macro: MacroType) -> HierarchyMacroSummary:
    return HierarchyMacroSummary(
        len(macro.atom_union), len(macro.node_types), macro.mdl_saving,
        normalized_macro_signature(macro), False)


def real_first_level_callbacks(
    *, maximum_nodes: int = 3,
) -> HierarchyCallbacks:
    """Bind the generic miner and the newly available macro promoter."""
    def mine(artifact: Any, level: int) -> MinedHierarchyLevel:
        result = mine_port_graph_macros(
            artifact, maximum_nodes=maximum_nodes)
        return MinedHierarchyLevel(
            len(artifact.prototypes),
            tuple(summarize_port_macro(macro)
                  for macro in result.macro_types), result.macro_types)

    def promote(artifact: Any, mined: MinedHierarchyLevel,
                level: int) -> Any:
        from materials_gcts_macro_promotion import promote_macro_types
        return promote_macro_types(
            artifact, mined.promotion_payload, level=level + 1)

    return HierarchyCallbacks(mine, promote)


def drive_recursive_port_hierarchy(
    initial_artifact: Any, callbacks: HierarchyCallbacks, *,
    maximum_levels: int = 16,
) -> RecursivePortHierarchy:
    """Mine/promote recursively and compare adjacent normalized productions."""
    if maximum_levels < 1:
        raise ValueError("maximum_levels must be positive")
    artifact = initial_artifact
    levels = []
    promotion_available = True
    termination = "level_limit"
    for level in range(maximum_levels):
        mined = callbacks.mine(artifact, level)
        positive = tuple(macro for macro in mined.macros
                         if macro.mdl_saving > 0)
        signatures = tuple(sorted(
            {macro.production_signature for macro in positive}, key=repr))
        certified = tuple(sorted(
            {macro.production_signature for macro in positive
             if macro.stationarity_certified}, key=repr))
        levels.append(HierarchyLevelRecord(
            level, mined.source_type_count, len(positive),
            tuple(sorted(macro.atom_support for macro in positive)),
            tuple(sorted(macro.child_support for macro in positive)),
            len(signatures), signatures, certified,
            sum(macro.mdl_saving for macro in positive)))
        if not positive:
            termination = "no_positive_mdl"
            break
        promoted = callbacks.promote(artifact, mined, level)
        if promoted is None:
            promotion_available = False
            termination = "promotion_unavailable"
            break
        artifact = promoted
    witnesses = []
    for lower, upper in zip(levels, levels[1:]):
        common = set(lower.certified_stationarity_signatures).intersection(
            upper.certified_stationarity_signatures)
        witnesses.extend(StationaryProductionWitness(
            lower.level, upper.level, signature)
            for signature in sorted(common, key=repr))
    return RecursivePortHierarchy(
        tuple(levels), tuple(witnesses), termination,
        termination == "no_positive_mdl", promotion_available,
        maximum_levels, True, True)
