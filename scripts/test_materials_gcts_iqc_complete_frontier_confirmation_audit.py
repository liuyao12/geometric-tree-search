#!/usr/bin/env python3

from materials_gcts_iqc_complete_frontier_confirmation_audit import evaluate


def test_fresh_complete_frontier_supply_and_portfolio_are_confirmed():
    report = evaluate()
    assert report.seed_atoms == 473
    assert report.target_atoms == 2048
    assert report.novel_target_atoms == 1575
    assert report.terminal_count == 128
    assert report.exact_terminal_count == 90
    assert report.portfolio_states == 18
    assert report.scalar_first_exact_rank == 1
    assert report.fusion_first_exact_rank == 1
    assert report.candidate_supply_confirmed
    assert report.rollback_portfolio_confirmed
    assert report.top_one_scalar_confirmed
    assert report.top_one_fusion_confirmed
    assert report.target_order_clean
    assert report.fresh_spatial_confirmation
    assert not report.stationary_or_exponential_claimed


if __name__ == "__main__":
    test_fresh_complete_frontier_supply_and_portfolio_are_confirmed()
    print("complete-frontier confirmation-audit tests passed")
