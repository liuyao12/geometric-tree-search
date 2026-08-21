#!/usr/bin/env python3

from materials_gcts_iqc_child_graph_future_option_audit import (
    load_default_result)


def test_group_heldout_child_graph_option_audit():
    row = load_default_result()
    assert row["supplied_heldout_groups"] == 9
    assert row["parent_examples"] == 1278
    assert row["exact_parent_examples"] == 142
    assert row["future_option_retained_groups"] == 8
    assert row["order2_top_parent_exact_groups"] == 8
    assert row["mean_option_first_exact_rank_sum"] == 30
    assert row["retention_p_value"] == .03125
    assert row["rank_p_value"] == .03125
    assert not row["causal_superiority_gate_passed"]
    assert len(row["folds"]) == 10
    assert all(len(fold["selected_parent_ids"]) == 4
               for fold in row["folds"])
    assert all(fold["retained_child_options"] >= 4
               for fold in row["folds"])
    assert row["every_channel_marginal_preserved"]
    assert row["candidate_geometry_unchanged"]
    assert not row["children_individually_labeled"]
    assert row["parent_labels_opened_only_after_selection"]
    assert not row["target_used_for_child_graph_or_ranking"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["third_block_child_correctness_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_group_heldout_child_graph_option_audit()
    print("IQC group-heldout child-graph future option: passed")
