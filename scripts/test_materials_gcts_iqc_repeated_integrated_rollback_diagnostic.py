#!/usr/bin/env python3
"""Regression for the repeated integrated-rollback consumed audit."""

from materials_gcts_iqc_repeated_integrated_rollback_diagnostic import (
    load_default_result)


def test_repeated_integrated_rollback_diagnostic():
    row = load_default_result()
    assert row["receipt"]["target_used"] is False
    assert row["receipt"]["repeated_rule"] == \
        ["integrated_frontier_vote_mass", 12]
    assert row["target_open_count"] == 1
    assert row["receipt"]["first_candidate_counts"] == [8, 37, 128]
    assert row["receipt"]["first_candidate_count"] == 128
    assert row["receipt"]["selected_stable_index"] == 115
    assert len(row["exact_first_stable_indices"]) == 16
    assert min(row["repeated_rule_exact_ranks"]) == 8
    assert row["repeated_rule_selects_exact_first"] is False
    assert row["second_block_same_rule_selects_exact"] is True
    assert row["consumed_two_block_rule_green"] is False
    assert row["target_used_for_rollout_or_ordering"] is False
    assert row["development_rule_selected_after_consumed_scoring"] is True
    assert row["consumed_target_diagnostic_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_repeated_integrated_rollback_diagnostic()
    print("repeated integrated-rollback diagnostic tests passed")
