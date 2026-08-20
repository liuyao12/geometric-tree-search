#!/usr/bin/env python3
"""Regression for the branch-local integrated rollback beam."""

from materials_gcts_iqc_branch_local_integrated_beam_diagnostic import (
    load_default_result)


def test_branch_local_integrated_beam():
    row = load_default_result()
    assert row["receipt"]["target_used"] is False
    assert row["receipt"]["first_beam_width"] == 8
    assert row["receipt"]["rollback_metric"] == \
        "integrated_frontier_vote_mass"
    assert row["receipt"]["rollout_horizon"] == 12
    assert row["target_open_count"] == 1
    assert row["receipt"]["global_parent_order"] == [3, 7, 1, 4, 5, 6, 8, 2]
    assert row["exact_end_to_end_branch_ranks"] == [8]
    assert row["branch_local_beam_contains_exact_path"] is True
    assert row["globally_selected_first_rank"] == 3
    assert row["globally_selected_first_exact"] is False
    assert row["globally_selected_second_exact"] is False
    assert row["globally_selected_end_to_end_exact"] is False
    assert row["target_used_for_candidate_rollout_or_ordering"] is False
    assert row["consumed_target_diagnostic_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_branch_local_integrated_beam()
    print("branch-local integrated beam tests passed")
