#!/usr/bin/env python3
"""Freeze the honest group-heldout recurrent-path selector result."""

from materials_gcts_iqc_recurrent_path_selector_audit import evaluate


def main():
    report = evaluate()
    assert report.training_groups == 10
    assert report.validation_groups == 8
    assert report.recurrent_prototypes == 455
    assert report.accepted_connection_states == 21841
    assert report.child_branching == 16
    assert report.selected_root_shortlist == 256
    assert report.selected_marking == (24, 5, 1.)
    assert report.selected_exact_by_group == (
        True, True, True, True, False, True, True, True)
    assert report.selected_exact_paths == 7
    assert report.candidate_supply_complete
    assert not report.autonomous_development_gate_passed
    assert report.descriptors_frozen_before_labels
    assert not report.target_used_for_candidate_generation
    assert report.candidate_digest == \
        "2c3233eeba7187a565baeee287042c9a8e44c77a6292be01e0ceebb9f07dee18"
    selected = next(row for row in report.audits if
                    row.root_shortlist == report.selected_root_shortlist and
                    (row.minimum_support, row.minimum_groups,
                     row.shrinkage) == report.selected_marking)
    assert selected.path_candidates_by_group == (
        391, 278, 318, 318, 293, 335, 325, 325)
    assert selected.exact_paths_by_group == (13, 2, 8, 8, 1, 14, 13, 13)
    assert selected.first_exact_ranks_by_group == (1, 1, 1, 1, 101, 1, 1, 1)
    assert report.cluster_compatibility_negative_ratio == 8
    assert report.cluster_compatibility_ridge == .1
    assert report.compatibility_selected_exact_by_group == (
        True, True, True, True, False, True, True, True)
    assert report.compatibility_first_exact_ranks == (
        1, 1, 1, 1, 21, 1, 1, 1)
    assert report.compatibility_selected_exact_paths == 7
    assert abs(report.compatibility_failed_rank_reduction - 101 / 21) < 1e-12
    assert report.compatibility_feature_digest == \
        "ce0fc44c95b2ebf4b0c6a0f5ddbd256cb0779d57f61e69a277b4b5a5777ac521"
    assert report.compatibility_model_digest == \
        "d8b17798276a1c3513a8aa40e5d6b82ef48f35b964d8d43e7012ac7eed4df35a"
    assert not report.cluster_compatibility_target_used
    assert not report.clusters_of_clusters_gate_passed
    print("recurrent IQC path selector audit passed")


if __name__ == "__main__":
    main()
