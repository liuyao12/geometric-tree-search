#!/usr/bin/env python3
"""Locate the earliest IQC beam stage that destroys exact terminal supply.

This consumed-development diagnostic preserves the frozen candidate geometry,
action reach, first-depth portfolio, scalar model, and graph-fusion model.  It
can retain the complete already-enumerated frontier from depth two onward, or
from the root onward.  Every candidate and both policy orders are frozen before
the previously consumed development targets are constructed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass

from materials_gcts_dual_rank_terminal_portfolio import (
    select_dual_rank_terminal_portfolio)
from materials_gcts_iqc_complete_terminal_frontier_audit import (
    _crop_all, _freeze_nucleus, _score)
from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, ORACLE_LIFT_BOUND, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_incidence_token_preflight import _key


DUAL_PORTFOLIO_BUDGET = 9


@dataclass(frozen=True)
class IQCProgressiveFrontierAudit:
    unpruned_from_depth: int
    preserved_frozen_depths: int
    action_reach_schedule: tuple[int, ...]
    nuclei: int
    terminal_counts: tuple[int, ...]
    candidate_counts_by_depth: tuple[tuple[int, ...], ...]
    retained_counts_by_depth: tuple[tuple[int, ...], ...]
    scalar_terminal_supply_by_center: tuple[bool, ...]
    scalar_selected_exact_by_center: tuple[bool, ...]
    scalar_selected_correct_by_center: tuple[int, ...]
    scalar_first_exact_rank_by_center: tuple[int | None, ...]
    fusion_terminal_supply_by_center: tuple[bool, ...]
    fusion_selected_exact_by_center: tuple[bool, ...]
    fusion_selected_correct_by_center: tuple[int, ...]
    fusion_first_exact_rank_by_center: tuple[int | None, ...]
    minimum_scalar_portfolio_for_complete_supply: int | None
    minimum_fusion_portfolio_for_complete_supply: int | None
    minimum_dual_portfolio_per_channel: int | None
    frozen_dual_portfolio_per_channel: int
    dual_portfolio_sizes_by_center: tuple[int, ...]
    dual_portfolio_exact_supply_by_center: tuple[bool, ...]
    dual_portfolio_exact_supply: int
    dual_portfolio_supply_gate_passed: bool
    scalar_terminal_supply: int
    scalar_selected_exact: int
    scalar_selected_correct: int
    fusion_terminal_supply: int
    fusion_selected_exact: int
    fusion_selected_correct: int
    previously_missing_nuclei_supplied: int
    complete_supply: bool
    incremental_fusion_advantage: bool
    candidates_frozen_before_targets: bool
    target_used_for_candidate_or_ranking: bool
    consumed_development_only: bool
    fresh_confirmation_claimed: bool
    stationary_or_exponential_claimed: bool
    receipt_digest: str
    honest_status: str


def evaluate(unpruned_from_depth: int = 1, root_reach: int = 4,
             second_reach: int = 4):
    if unpruned_from_depth not in (0, 1):
        raise ValueError("progressive audit supports root or second-depth widening")
    if root_reach < 1 or second_reach < 1:
        raise ValueError("action reaches must be positive")
    schedule = (root_reach, second_reach, 8)
    runtime = load_default_runtime()
    seeds = _crop_all(SEED_RADIUS, ORACLE_LIFT_BOUND)
    nuclei = tuple(_freeze_nucleus(
        runtime, center, seed, unpruned_from_depth=unpruned_from_depth,
        schedule=schedule)
        for center, seed in zip(DEVELOPMENT_CENTERS, seeds))
    portfolios = tuple(select_dual_rank_terminal_portfolio(
        tuple(terminal.actions for terminal in row.terminals),
        row.scalar_order, row.fusion_order,
        per_channel_budget=DUAL_PORTFOLIO_BUDGET) for row in nuclei)
    receipt = tuple((
        row.center, row.seed_atoms, row.candidate_counts_by_depth,
        row.retained_counts_by_depth, row.candidate_digest,
        tuple(terminal.actions for terminal in row.terminals),
        row.scalar_order, row.fusion_order,
        portfolio.selection_digest, portfolio.selected_candidate_ids)
        for row, portfolio in zip(nuclei, portfolios))
    receipt_digest = hashlib.sha256(repr(receipt).encode()).hexdigest()
    immutable = repr(receipt)

    targets = _crop_all(TARGET_RADIUS, ORACLE_LIFT_BOUND)
    scalar, fusion = [], []
    portfolio_supply = []
    for nucleus, portfolio, target in zip(nuclei, portfolios, targets):
        truth = {_key(point): str(color) for point, color in
                 zip(target.positions, target.species)}
        scalar.append(_score(nucleus, nucleus.scalar_order, truth))
        fusion.append(_score(nucleus, nucleus.fusion_order, truth))
        exact = tuple(all(truth.get(_key(point)) == color
                          for point, color in terminal.actions)
                      for terminal in nucleus.terminals)
        portfolio_supply.append(any(
            exact[index] for index in portfolio.selected_indices))
    if immutable != repr(receipt):
        raise AssertionError("progressive candidate receipt changed after scoring")

    scalar_supply = sum(row[0] for row in scalar)
    scalar_exact = sum(row[1] for row in scalar)
    scalar_correct = sum(row[2] for row in scalar)
    fusion_supply = sum(row[0] for row in fusion)
    fusion_exact = sum(row[1] for row in fusion)
    fusion_correct = sum(row[2] for row in fusion)
    complete = fusion_supply == len(nuclei)
    incremental = fusion_exact > scalar_exact or fusion_correct > scalar_correct
    scalar_ranks = tuple(row[3] for row in scalar)
    fusion_ranks = tuple(row[3] for row in fusion)
    minimum_scalar = max(scalar_ranks) if all(scalar_ranks) else None
    minimum_fusion = max(fusion_ranks) if all(fusion_ranks) else None
    minimum_dual = next((budget for budget in range(1, max(
        max((rank or 0) for rank in scalar_ranks),
        max((rank or 0) for rank in fusion_ranks)) + 1)
        if all((scalar_rank is not None and scalar_rank <= budget)
               or (fusion_rank is not None and fusion_rank <= budget)
               for scalar_rank, fusion_rank in
               zip(scalar_ranks, fusion_ranks))), None)
    stage = "root" if unpruned_from_depth == 0 else "second-depth"
    return IQCProgressiveFrontierAudit(
        unpruned_from_depth, unpruned_from_depth, schedule, len(nuclei),
        tuple(len(row.terminals) for row in nuclei),
        tuple(row.candidate_counts_by_depth for row in nuclei),
        tuple(row.retained_counts_by_depth for row in nuclei),
        tuple(row[0] for row in scalar), tuple(row[1] for row in scalar),
        tuple(row[2] for row in scalar), tuple(row[3] for row in scalar),
        tuple(row[0] for row in fusion), tuple(row[1] for row in fusion),
        tuple(row[2] for row in fusion), tuple(row[3] for row in fusion),
        minimum_scalar, minimum_fusion, minimum_dual,
        DUAL_PORTFOLIO_BUDGET,
        tuple(len(row.selected_indices) for row in portfolios),
        tuple(portfolio_supply), sum(portfolio_supply),
        all(portfolio_supply),
        scalar_supply, scalar_exact, scalar_correct,
        fusion_supply, fusion_exact, fusion_correct,
        fusion_supply - 6, complete, incremental, True, False, True,
        False, False, receipt_digest,
        (f"complete {stage} frontier restores exact supply on every nucleus"
         if complete else
         f"complete {stage} frontier still lacks exact terminal supply"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unpruned-from-depth", type=int, choices=(0, 1),
                        default=1)
    parser.add_argument("--root-reach", type=int, default=4)
    parser.add_argument("--second-reach", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(
        args.unpruned_from_depth, args.root_reach, args.second_reach)
    print(json.dumps(asdict(report), indent=2, sort_keys=True)
          if args.json else report)


if __name__ == "__main__":
    main()
