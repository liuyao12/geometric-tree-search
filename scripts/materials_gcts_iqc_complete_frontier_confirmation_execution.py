#!/usr/bin/env python3
"""Target-free execution adapter for widened IQC frontier confirmation.

The caller supplies only a colored seed and public center.  The adapter loads
the already frozen grammar/value artifact, enumerates the complete bounded
``8 -> 8 -> 8`` tree, freezes both immutable terminal orders, and retains the
top-nine union as a rollback portfolio.  It deliberately exposes no target or
scorer argument.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import SimpleNamespace

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_complete_terminal_frontier_audit import (
    CompleteTerminalNucleus, _freeze_nucleus)
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime


ACTION_REACH_SCHEDULE = (8, 8, 8)
UNPRUNED_FROM_DEPTH = 0
DUAL_PORTFOLIO_BUDGET = 9


@dataclass(frozen=True)
class FrozenCompleteFrontierConfirmation:
    center: tuple[float, float, float]
    seed_atoms: int
    action_reach_schedule: tuple[int, ...]
    unpruned_from_depth: int
    candidate_counts_by_depth: tuple[int, ...]
    terminal_count: int
    terminal_actions: tuple[tuple, ...]
    scalar_order: tuple[int, ...]
    fusion_order: tuple[int, ...]
    per_channel_portfolio_budget: int
    portfolio_indices: tuple[int, ...]
    portfolio_actions: tuple[tuple, ...]
    candidate_digest: str
    portfolio_digest: str
    execution_digest: str
    target_used: bool = False


def _freeze_receipt(nucleus: CompleteTerminalNucleus):
    candidate_ids = tuple(terminal.actions for terminal in nucleus.terminals)
    portfolio = select_dual_rank_terminal_portfolio(
        candidate_ids, nucleus.scalar_order, nucleus.fusion_order,
        per_channel_budget=DUAL_PORTFOLIO_BUDGET)
    payload = (
        nucleus.center, nucleus.seed_atoms, ACTION_REACH_SCHEDULE,
        UNPRUNED_FROM_DEPTH, nucleus.candidate_counts_by_depth,
        candidate_ids, nucleus.scalar_order, nucleus.fusion_order,
        DUAL_PORTFOLIO_BUDGET, portfolio.selected_candidate_ids,
        nucleus.candidate_digest, portfolio.selection_digest)
    digest = hashlib.sha256(repr(payload).encode()).hexdigest()
    return FrozenCompleteFrontierConfirmation(
        nucleus.center, nucleus.seed_atoms, ACTION_REACH_SCHEDULE,
        UNPRUNED_FROM_DEPTH, nucleus.candidate_counts_by_depth,
        len(nucleus.terminals), candidate_ids, nucleus.scalar_order,
        nucleus.fusion_order, DUAL_PORTFOLIO_BUDGET,
        portfolio.selected_indices, portfolio.selected_candidate_ids,
        nucleus.candidate_digest, portfolio.selection_digest, digest)


def freeze_confirmation_candidates(*, center, seed_positions, seed_species):
    if len(seed_positions) != len(seed_species) or not seed_positions:
        raise ValueError("seed positions/species must be nonempty and aligned")
    seed = SimpleNamespace(
        positions=tuple(tuple(map(float, point)) for point in seed_positions),
        species=tuple(map(str, seed_species)))
    nucleus = _freeze_nucleus(
        load_default_runtime(), tuple(map(float, center)), seed,
        unpruned_from_depth=UNPRUNED_FROM_DEPTH,
        schedule=ACTION_REACH_SCHEDULE)
    return _freeze_receipt(nucleus)


__all__ = [
    "ACTION_REACH_SCHEDULE", "DUAL_PORTFOLIO_BUDGET",
    "FrozenCompleteFrontierConfirmation", "freeze_confirmation_candidates"]
