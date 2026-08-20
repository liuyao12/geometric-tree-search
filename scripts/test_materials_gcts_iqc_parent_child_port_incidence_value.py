#!/usr/bin/env python3
"""Regression for identity-preserving IQC port-transition value."""

from materials_gcts_iqc_parent_child_port_incidence_value import (
    load_default_result)


def test_parent_child_port_incidence_value():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["exact_examples"] == 142
    assert row["cached_graph_embeddings"] == 1120
    assert row["nested_supplied_groups"] == 9
    assert row["nested_selected_exact_groups"] == 7
    assert row["nested_selected_correct_sites"] == 26
    assert row["shuffle_p"] == .03125
    assert row["confirmation"]["order"] == [4, 8, 5, 1, 6, 7, 3, 2]
    assert row["confirmation"]["exact_path_ranks"] == [2]
    assert row["confirmation"]["selected_end_to_end_exact"] is False
    assert row["identity_preserving_incidence_used"] is True
    assert row["raw_type_ids_in_graph"] is False
    assert row["candidate_geometry_unchanged"] is True
    assert row["target_used_for_fit_or_ranking"] is False
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_parent_child_port_incidence_value()
    print("IQC parent-child port-incidence value tests passed")
