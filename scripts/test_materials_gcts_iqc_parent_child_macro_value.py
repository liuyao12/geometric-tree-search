#!/usr/bin/env python3
"""Regression for the IQC parent→child macro value."""

from materials_gcts_iqc_parent_child_macro_value import load_default_result


def test_parent_child_macro_value():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["exact_examples"] == 142
    assert row["nested_supplied_groups"] == 9
    assert row["nested_selected_exact_groups"] == 1
    assert row["nested_selected_correct_sites"] == 14
    assert row["development_selected_exact_groups"] == 6
    assert row["development_selected_correct_sites"] == 25
    assert row["final_representation"] == "cross-geometry"
    assert row["final_ridge"] == .25
    assert row["shuffle_p"] == .03125
    assert row["confirmation"]["order"] == [2, 4, 3, 8, 7, 5, 1, 6]
    assert row["confirmation"]["exact_path_ranks"] == [4]
    assert row["confirmation"]["selected_end_to_end_exact"] is False
    assert row["candidate_geometry_unchanged"] is True
    assert row["target_used_for_macro_fit_or_ranking"] is False
    assert row["targets_consumed_development_only"] is True
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_parent_child_macro_value()
    print("parent-child macro value tests passed")
