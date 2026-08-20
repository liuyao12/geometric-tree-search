#!/usr/bin/env python3
"""Regression for the consumed deferred-pruning portfolio-rank audit."""

from materials_gcts_iqc_post_self_fed_deferred_pruning_portfolio_rank import (
    load_default_result)


def test_deferred_pruning_portfolio_rank():
    row = load_default_result()
    assert row["receipt"]["target_used"] is False
    assert row["receipt"]["consumed_first_rank"] == 8
    assert row["target_open_count"] == 1
    assert len(row["exact_second_stable_indices"]) == 4
    assert row["exact_second_stable_indices"] == [86, 87, 89, 123]
    assert row["exact_ranks_by_marking"]["typed_child_topology"] == \
        [62, 98, 63, 88]
    assert row["exact_ranks_by_marking"]["local_section_ordinal_yield"] == \
        [108, 121, 100, 98]
    assert row["minimum_per_marking_depth_for_exact_supply"] == 62
    assert row["maximum_portfolio_actions_at_minimum_depth"] == 124
    assert row["current_top_one_per_marking_retains_exact"] is False
    assert row["target_used_for_ordering"] is False
    assert row["consumed_target_diagnostic_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_deferred_pruning_portfolio_rank()
    print("deferred-pruning portfolio-rank tests passed")
