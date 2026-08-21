#!/usr/bin/env python3

from materials_gcts_iqc_marking_portfolio_audit import evaluate


def test_two_mark_portfolio_repairs_candidate_loss_not_value():
    report = evaluate()
    assert report.development_groups == 20
    assert report.development_execution_candidates == 160
    assert report.development_exact_supply_groups == 19
    assert report.connection_exact_groups == 19
    assert report.rollout_exact_groups == 19
    assert report.portfolio_exact_groups == 19
    assert not report.portfolio_loses_an_exact_head
    assert report.confirmation_candidate_count == 8
    assert report.confirmation_connection_index == 0
    assert report.confirmation_rollout_index == 7
    assert report.confirmation_heads_differ
    assert set(report.confirmation_retained_indices) == {0, 7}
    assert report.confirmation_exact_retained == 1
    assert report.confirmation_inexact_retained == 1
    assert report.confirmation_exact_connection_head_preserved
    assert not report.confirmation_target_reopened
    assert report.identical_candidate_tree_for_both_markings
    assert not report.winner_selected
    assert not report.autonomous_growth_claimed
    assert not report.stationary_or_exponential_claimed
    assert report.portfolio_supply_gate_passed


if __name__ == "__main__":
    test_two_mark_portfolio_repairs_candidate_loss_not_value()
    print("IQC marking portfolio candidate-supply audit passed")
