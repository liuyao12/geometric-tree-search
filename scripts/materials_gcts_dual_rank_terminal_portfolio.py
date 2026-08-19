#!/usr/bin/env python3
"""Freeze a bounded union of two target-free terminal rankings.

The selector does not generate geometry, score candidates, inspect targets, or
choose a winning terminal.  It preserves exact candidate identities from the
top ``k`` positions of each independently frozen order so a later tree search
can validate, backtrack, or continue those alternatives.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class DualRankTerminalPortfolio:
    candidate_count: int
    per_channel_budget: int
    scalar_head: tuple[int, ...]
    fusion_head: tuple[int, ...]
    selected_indices: tuple[int, ...]
    selected_candidate_ids: tuple[Hashable, ...]
    candidate_digest: str
    selection_digest: str
    target_used: bool = False


def _validate_order(name: str, order: Sequence[int], size: int):
    frozen = tuple(map(int, order))
    if len(frozen) != size or set(frozen) != set(range(size)):
        raise ValueError(f"{name} must be a permutation of candidate indices")
    return frozen


def select_dual_rank_terminal_portfolio(
        candidate_ids: Sequence[Hashable], scalar_order: Sequence[int],
        fusion_order: Sequence[int], *, per_channel_budget: int
) -> DualRankTerminalPortfolio:
    ids = tuple(candidate_ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("candidate IDs must be nonempty and unique")
    if per_channel_budget <= 0:
        raise ValueError("per_channel_budget must be positive")
    scalar = _validate_order("scalar_order", scalar_order, len(ids))
    fusion = _validate_order("fusion_order", fusion_order, len(ids))
    budget = min(int(per_channel_budget), len(ids))
    scalar_head, fusion_head = scalar[:budget], fusion[:budget]

    selected = []
    seen = set()
    for rank in range(budget):
        for index in (scalar_head[rank], fusion_head[rank]):
            if index in seen:
                continue
            seen.add(index)
            selected.append(index)
    selected = tuple(selected)
    selected_ids = tuple(ids[index] for index in selected)
    candidate_digest = hashlib.sha256(repr(ids).encode()).hexdigest()
    selection_digest = hashlib.sha256(repr((
        candidate_digest, budget, scalar_head, fusion_head,
        selected_ids)).encode()).hexdigest()
    return DualRankTerminalPortfolio(
        len(ids), budget, scalar_head, fusion_head, selected, selected_ids,
        candidate_digest, selection_digest)


__all__ = [
    "DualRankTerminalPortfolio", "select_dual_rank_terminal_portfolio"]
