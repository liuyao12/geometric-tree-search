#!/usr/bin/env python3
"""Frozen-result regression for the one-shot IQC rollback confirmation."""

from materials_gcts_iqc_post_self_fed_rollback_confirmation import (
    load_default_result)


def test_fresh_rollback_confirmation_result():
    row = load_default_result()
    assert row["receipt"]["target_used"] is False
    assert row["receipt"]["target_open_count_before_receipt"] == 0
    assert row["target_open_count"] == 1
    assert row["domain_disjoint"] is True
    assert row["first_correct_actions"] == 2
    assert row["second_correct_actions"] == 1
    assert row["end_to_end_correct_actions"] == 3
    assert row["portfolio_contains_exact_second_block"] is False
    assert row["rollback_selected_exact_second_block"] is False
    assert row["fresh_confirmation_passed"] is False
    assert row["autonomous_finite_two_block_commit_gate_passed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_fresh_rollback_confirmation_result()
    print("fresh rollback confirmation result tests passed")
