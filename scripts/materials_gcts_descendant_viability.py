#!/usr/bin/env python3
"""Backward viability labels for a frozen, bounded GCTS search tree.

The label is causal with respect to execution: candidate geometry and parent
edges are frozen first.  Training truth may then identify successful terminal
nodes, and viability is propagated only through the parent edges that actually
generated those terminals.  At replay, the fitted value sees invariant node
features and action colours; terminal truth and target sites are not APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class FrozenViabilityNode:
    group: Hashable
    key: Hashable
    parent_key: Hashable | None
    features: tuple[float, ...]
    action_colors: tuple[str, ...]


@dataclass(frozen=True)
class DescendantViabilityExample:
    group: Hashable
    stage: int
    key: Hashable
    features: tuple[float, ...]
    action_colors: tuple[str, ...]
    viable: bool


@dataclass(frozen=True)
class DescendantViabilityAudit:
    stages: int
    nodes_by_stage: tuple[int, ...]
    viable_by_stage: tuple[int, ...]
    successful_terminals: int
    all_parent_edges_frozen: bool
    target_used_during_tree_construction: bool = False


def label_descendant_viability(
        stages: Sequence[Sequence[FrozenViabilityNode]],
        successful_terminal_keys: Sequence[Hashable],
        ) -> tuple[tuple[tuple[DescendantViabilityExample, ...], ...],
                   DescendantViabilityAudit]:
    """Propagate terminal success backward through exact frozen parent edges."""
    levels = tuple(tuple(level) for level in stages)
    if not levels or any(not level for level in levels):
        raise ValueError("empty frozen viability tree")
    groups = {node.group for level in levels for node in level}
    if len(groups) != 1:
        raise ValueError("one frozen tree must belong to one spatial group")
    tables = []
    for stage, level in enumerate(levels):
        table = {node.key: node for node in level}
        if len(table) != len(level):
            raise ValueError("duplicate node key within a viability stage")
        if any(not node.features or not node.action_colors
               for node in level):
            raise ValueError("empty viability feature payload")
        if stage and any(node.parent_key not in tables[-1]
                         for node in level):
            raise ValueError("viability edge does not reference prior stage")
        tables.append(table)
    successful = set(successful_terminal_keys)
    if not successful or not successful <= set(tables[-1]):
        raise ValueError("successful terminal keys are not frozen terminals")
    viable = [set() for _level in levels]
    viable[-1] = successful
    for stage in range(len(levels) - 1, 0, -1):
        viable[stage - 1].update(
            tables[stage][key].parent_key for key in viable[stage])
    examples = tuple(tuple(DescendantViabilityExample(
        node.group, stage, node.key, node.features, node.action_colors,
        node.key in viable[stage]) for node in level)
        for stage, level in enumerate(levels))
    audit = DescendantViabilityAudit(
        len(levels), tuple(map(len, levels)),
        tuple(len(keys) for keys in viable), len(successful), True, False)
    return examples, audit
