#!/usr/bin/env python3

from materials_gcts_iqc_branch_action_graph_audit import evaluate


def test_complete_branch_graph_is_locally_identifying_but_not_transferable():
    row = evaluate()
    assert row["development_groups"] == 10
    assert row["supplied_groups"] == 9
    assert (row["branches"], row["exact_branches"],
            row["false_branches"]) == (120, 59, 61)
    assert row["canonical_branch_graph_classes"] == 119
    assert row["repeated_branch_graph_classes"] == 1
    assert row["heldout_exact_graph_rows"] == 2
    assert row["heldout_graph_rows"] == 2
    assert row["forward_unsatisfied_branches"] == 28
    assert row["forward_unsatisfied_groups"] == 3
    assert row["forward_unsatisfied_exact_groups"] == 2
    assert row["forward_unsatisfied_within_group_graph_classes"] == 28
    assert row["selected_endpoint_classes"] == 3
    assert row["selected_endpoint_exact_false_mixed_classes"] == 2
    assert row["branch_graph_exact_false_collisions_within_group"] == 0
    assert row["knn_feature_count"] == 30
    assert row["knn_candidate_neighbors"] == (1, 3, 5, 9, 15)
    assert row["knn_selected_neighbors_by_group"] == (15, 1, 1)
    assert row["knn_selected_exact_groups"] == 0
    assert row["knn_shuffle_trials"] == 31
    assert row["knn_shuffle_exact_median"] == 0
    assert row["knn_shuffle_exact_maximum"] == 1
    assert row["knn_empirical_p"] == 1.
    assert row["edge_selected_widths_by_group"] == (2., 4., .25)
    assert row["edge_selected_exact_groups"] == 0
    assert row["edge_shuffle_trials"] == 31
    assert row["edge_shuffle_exact_median"] == 0
    assert row["edge_shuffle_exact_maximum"] == 1
    assert row["edge_empirical_p"] == 1.
    assert row["candidate_geometry_unchanged"]
    assert not row["raw_occurrence_or_stable_index_used_as_feature"]
    assert not row["target_used_for_graph_or_fit"]
    assert row["development_labels_used_for_model_selection"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["integrated_as_default_marking"]
    assert row["local_identifiability_gate_passed"]
    assert not row["transferable_graph_marking_gate_passed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_complete_branch_graph_is_locally_identifying_but_not_transferable()
    print("IQC branch action-graph audit passed")
