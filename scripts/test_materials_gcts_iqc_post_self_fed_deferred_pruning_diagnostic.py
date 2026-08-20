#!/usr/bin/env python3
"""Regression for the consumed-target deferred-pruning diagnostic."""

from materials_gcts_iqc_post_self_fed_deferred_pruning_diagnostic import (
    load_default_result)


def test_deferred_pruning_diagnostic():
    row = load_default_result()
    assert row["receipt"]["target_used"] is False
    assert row["receipt"]["first_retained_width"] == 8
    assert row["receipt"]["first_candidate_counts"] == [8, 37, 128]
    assert row["receipt"]["first_candidate_count"] == 128
    assert row["first_exact_ranks_in_width"] == [8]
    assert row["cross_block_candidate_exact_supply"] is True
    assert row["cross_block_portfolio_exact_supply"] is False
    assert len(row["cross_block_candidate_exact_paths"]) == 4
    assert row["cross_block_portfolio_exact_paths"] == []
    assert row["target_open_count"] == 1
    assert row["target_used_for_candidate_or_portfolio_selection"] is False
    assert row["consumed_target_diagnostic_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_deferred_pruning_diagnostic()
    print("deferred-pruning diagnostic tests passed")
