#!/usr/bin/env python3
"""Regression for complete-frontier deferred rollback ranking."""

from materials_gcts_iqc_post_self_fed_deferred_pruning_rollout_rank import (
    load_default_result)


def test_deferred_pruning_rollout_rank():
    row = load_default_result()
    assert row["receipt"]["target_used"] is False
    assert row["receipt"]["consumed_first_rank"] == 8
    assert row["receipt"]["rollback_metric"] == "frontier_vote_mass"
    assert row["receipt"]["rollback_horizon"] == 12
    assert row["target_open_count"] == 1
    assert len(row["exact_second_stable_indices"]) == 4
    assert row["exact_second_stable_indices"] == [86, 87, 89, 123]
    assert row["exact_rollback_ranks"] == [32, 19, 33, 124]
    assert row["best_exact_rollback_rank"] == 19
    assert row["top_one_rollback_retains_exact"] is False
    assert row["top_eight_rollback_retains_exact"] is False
    assert row["top_sixteen_rollback_retains_exact"] is False
    assert row["exact_ranks_by_predeclared_rule"][
        "integrated_frontier_vote_mass@12"] == [17, 21, 1, 33]
    assert row["integrated_vote_mass_h12_retains_exact"] is True
    assert row["development_rule_selected_after_consumed_scoring"] is True
    assert row["target_used_for_rollout_or_ordering"] is False
    assert row["consumed_target_diagnostic_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_deferred_pruning_rollout_rank()
    print("deferred-pruning rollout-rank tests passed")
