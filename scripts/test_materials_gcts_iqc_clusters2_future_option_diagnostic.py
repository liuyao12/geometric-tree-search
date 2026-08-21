#!/usr/bin/env python3

from materials_gcts_iqc_clusters2_future_option_diagnostic import (
    CHANNEL_NAMES, load_default_result)


def test_consumed_clusters2_future_option_supply():
    row = load_default_result()
    receipt = row["receipt"]
    assert receipt["target_used"] is False
    assert receipt["target_open_count_before_receipt"] == 0
    assert receipt["channel_names"] == list(CHANNEL_NAMES)
    assert receipt["top_k_children"] == 8
    assert receipt["parent_beam_width"] == 4
    assert receipt["selected_parent_ids"] == [7, 1, 8, 5]
    assert receipt["selected_by_channels"] == [
        ["base", 7], ["colored", 1], ["ports", 8], ["coupled", 5]]
    assert row["exact_parent_ids"] == [8]
    assert row["exact_path_parent_ids"] == [8]
    assert row["retained_exact_path_parent_ids"] == [8]
    assert row["future_option_retains_exact_path"] is True
    assert row["retained_exact_parent_child_paths"] == [[8, [8, 123]]]
    assert row["future_option_child_portfolio_retains_exact_path"] is True
    assert row["mean_option_first_exact_rank"] == 3
    assert row["channel_first_exact_ranks"] == [5, 5, 1, 2]
    exact = next(value for value in row["scored_parents"]
                 if value["parent_id"] == 8)
    assert exact["channel_exact_children_in_top_k"] == [1, 0, 0, 0]
    assert not any(exact["channel_best_child_exact"])
    assert row["candidate_geometry_unchanged"] is True
    assert row["target_used_for_tree_or_ranking"] is False
    assert row["consumed_target_diagnostic_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_consumed_clusters2_future_option_supply()
    print("consumed clusters-squared future-option supply: passed")
