#!/usr/bin/env python3

import inspect
from types import SimpleNamespace

from materials_gcts_iqc_complete_frontier_confirmation_execution import (
    ACTION_REACH_SCHEDULE, DUAL_PORTFOLIO_BUDGET, _freeze_receipt,
    freeze_confirmation_candidates)


def test_execution_api_has_no_target_or_scorer():
    parameters = inspect.signature(freeze_confirmation_candidates).parameters
    assert set(parameters) == {"center", "seed_positions", "seed_species"}
    assert not ({"target", "truth", "oracle", "scorer"} & set(parameters))
    assert ACTION_REACH_SCHEDULE == (8, 8, 8)
    assert DUAL_PORTFOLIO_BUDGET == 9


def test_receipt_freezes_dual_order_union_without_target():
    terminals = tuple(SimpleNamespace(actions=((float(index), 0., 0., "X"),))
                      for index in range(12))
    nucleus = SimpleNamespace(
        center=(1., 2., 3.), seed_atoms=20,
        candidate_counts_by_depth=(8, 30, 12), terminals=terminals,
        scalar_order=tuple(range(12)),
        fusion_order=tuple(reversed(range(12))),
        candidate_digest="a" * 64)
    receipt = _freeze_receipt(nucleus)
    assert receipt.terminal_count == 12
    assert len(receipt.portfolio_indices) == 12
    assert set(receipt.portfolio_actions) == set(receipt.terminal_actions)
    assert len(receipt.execution_digest) == 64
    assert not receipt.target_used


if __name__ == "__main__":
    test_execution_api_has_no_target_or_scorer()
    test_receipt_freezes_dual_order_union_without_target()
    print("complete-frontier confirmation-execution tests passed")
