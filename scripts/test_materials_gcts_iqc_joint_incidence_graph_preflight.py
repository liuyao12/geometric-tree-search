#!/usr/bin/env python3
"""Regression for explicit IQC joint role-incidence geometry."""

from materials_gcts_iqc_joint_incidence_graph_preflight import (
    JointFitSpec, evaluate)


def test_joint_incidence_edges_transfer_but_marginal_scoring_stays_red():
    report = evaluate()
    assert report.candidate_graph_digest == \
        "ddd96b159b0c3d8cbdfbc64b90ba583c17a6afd8cbdd31d93aead66b5a56e8c3"
    assert report.descriptor_digest == \
        "45de5caafdb5a600d8ad5f5e0f9b3148f31f1abda68e6e3cdf71f5ae047e8282"
    assert report.joint_role_shell_tokens == 6140
    assert report.joint_role_metric_edge_tokens == 19837
    assert report.selected_fit == JointFitSpec(4, 2, .5)
    assert report.selected_correct_by_group == \
        (2, 0, 2, 2, 2, 2, 2, 2, 1, 0)
    assert report.selected_actions == 20
    assert report.selected_correct_actions == 15
    assert report.selected_false_actions == 5
    assert report.exact_groups == 7
    assert report.mean_weighted_token_fraction > .976
    assert tuple(row.selected_correct_actions for row in report.fit_audits) == \
        (15, 14, 14, 14, 14, 8)
    assert report.selection_target_free is True
    assert report.exact_candidate_geometry_changed is False
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_joint_incidence_edges_transfer_but_marginal_scoring_stays_red()
    print("IQC joint incidence graph preflight regression passed")


if __name__ == "__main__":
    main()
