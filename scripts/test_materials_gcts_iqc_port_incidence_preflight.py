#!/usr/bin/env python3
"""Slow exact regression for the train-only IQC incidence preflight."""

from materials_gcts_iqc_port_incidence_preflight import evaluate


def test_real_iqc_incidence_preflight():
    report = evaluate()
    assert report.reserved_confirmation_center_imported_or_accessed is False
    assert report.action_graph_digest == \
        "21f6c9a5aa54b59c81ca7d38664655101cbd68bf80bc9f0e043c5565c3f941d6"
    assert report.total_actions == 504
    assert report.positive_actions == 23
    assert len(report.selected_paths) == len(report.training_centers)
    assert report.complete_two_action_paths == 8
    assert report.selected_actions == 16
    assert report.selected_correct_actions == 0
    assert report.selected_false_actions == 16
    assert report.selected_correct_sites == 0
    assert report.selected_false_sites == 120
    assert report.backtracks == 49
    assert report.explored_actions == 306
    assert report.selected_actions == (
        report.selected_correct_actions + report.selected_false_actions)
    assert abs(report.heldout_seen_role_fraction -
               .974029425424061) < 1e-12
    assert report.heldout_admitted_role_fraction == 0.
    assert report.preflight_passed is False


if __name__ == "__main__":
    test_real_iqc_incidence_preflight()
    print("IQC port incidence preflight test passed")
