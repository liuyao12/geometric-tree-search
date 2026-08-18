#!/usr/bin/env python3
"""Regression for directed root-to-child IQC successor values."""

from materials_gcts_iqc_path_conditioned_successor_audit import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.path_branching == 4
    assert set(report.heldout_paths_by_group) == {64}
    assert report.additive_baseline_correct_actions == 30
    assert report.one_step_successor_correct_actions == 31
    assert report.pooled_two_step_correct_actions == 31
    assert report.selected_correct_actions == 33
    assert report.selected_false_actions == 3
    assert report.exact_groups == 15
    assert report.selected_correct_by_group == (
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 1, 2, 2, 2)
    assert report.path_descriptor_digest == \
        "3475ab98aa4375ada07f847efa735ce8048d814318dbb3580703895115a543d3"
    assert report.path_descriptors_constructed_before_labels
    assert not report.exact_candidate_geometry_changed
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("path-conditioned IQC successor regression passed")


if __name__ == "__main__":
    main()
