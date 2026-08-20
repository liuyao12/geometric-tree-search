#!/usr/bin/env python3
"""Regression for the IQC boundary-obligation transition value."""

from materials_gcts_iqc_parent_child_port_transition_value import (
    load_default_result)


def test_parent_child_port_transition_value():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["exact_examples"] == 142
    assert row["feature_count"] == 131
    assert row["nested_supplied_groups"] == 9
    assert row["nested_selected_exact_groups"] == 3
    assert row["nested_selected_correct_sites"] == 20
    assert row["shuffle_p"] == .1875
    assert row["final_representation"] == "macro+port-delta"
    assert row["confirmation"]["order"] == [4, 2, 3, 7, 8, 1, 6, 5]
    assert row["confirmation"]["exact_path_ranks"] == [5]
    assert row["confirmation"]["selected_end_to_end_exact"] is False
    assert row["raw_type_ids_in_features"] is False
    assert row["candidate_geometry_unchanged"] is True
    assert row["target_used_for_fit_or_ranking"] is False
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_parent_child_port_transition_value()
    print("parent-child port-transition value tests passed")
