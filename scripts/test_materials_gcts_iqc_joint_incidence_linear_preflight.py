#!/usr/bin/env python3
"""Regression for the nested joint-incidence scalar-stack control."""

from materials_gcts_iqc_joint_incidence_linear_preflight import evaluate


def test_nested_scalar_stack_fails_without_opening_next_confirmation():
    report = evaluate()
    assert report.candidate_graph_digest == \
        "ddd96b159b0c3d8cbdfbc64b90ba583c17a6afd8cbdd31d93aead66b5a56e8c3"
    assert report.feature_digest == \
        "1db653ec3eac064ef8c654b521365c6b47740932dca1df97d2719b6895a44b3f"
    assert tuple(row.correct_actions for row in report.ridge_audits) == (0, 0, 0)
    assert tuple(row.false_actions for row in report.ridge_audits) == (20, 20, 20)
    assert report.selected_correct_by_group == (0,) * 10
    assert report.selected_actions == 20
    assert report.selected_correct_actions == 0
    assert report.selected_false_actions == 20
    assert report.outer_labels_used_for_fit_or_selection is False
    assert report.exact_candidate_geometry_changed is False
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_nested_scalar_stack_fails_without_opening_next_confirmation()
    print("IQC joint-incidence linear preflight regression passed")


if __name__ == "__main__":
    main()
