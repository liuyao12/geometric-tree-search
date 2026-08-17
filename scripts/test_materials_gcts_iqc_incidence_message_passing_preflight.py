#!/usr/bin/env python3
"""Regression for bounded IQC incidence message passing."""

from materials_gcts_iqc_incidence_message_passing_preflight import evaluate


def test_exact_message_colors_fragment_and_remain_below_gate():
    report = evaluate()
    assert report.candidate_graph_digest == \
        "ddd96b159b0c3d8cbdfbc64b90ba583c17a6afd8cbdd31d93aead66b5a56e8c3"
    assert report.message_rounds == (1, 2)
    assert tuple(row.selected_correct_actions
                 for row in report.round_audits) == (14, 14)
    assert tuple(row.message_node_types
                 for row in report.round_audits) == (80323, 161768)
    assert tuple(row.message_graph_types
                 for row in report.round_audits) == (12070, 24140)
    assert report.selected_rounds == 1
    assert report.selected_correct_by_group == \
        (2, 0, 2, 2, 2, 2, 2, 2, 0, 0)
    assert report.selected_actions == 20
    assert report.selected_correct_actions == 14
    assert report.selected_false_actions == 6
    assert report.exact_groups == 7
    assert report.bounded_message_passing is True
    assert report.selection_target_free is True
    assert report.exact_candidate_geometry_changed is False
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_exact_message_colors_fragment_and_remain_below_gate()
    print("IQC incidence message-passing preflight regression passed")


if __name__ == "__main__":
    main()
