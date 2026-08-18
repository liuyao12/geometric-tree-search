#!/usr/bin/env python3
"""Regression for bounded target-free two-step IQC successor rollout."""

from materials_gcts_iqc_two_step_successor_value_audit import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.rollout_branching == 4
    assert report.additive_baseline_correct_actions == 30
    assert report.one_step_successor_correct_actions == 31
    assert report.selected_correct_actions == 31
    assert report.selected_false_actions == 5
    assert report.exact_groups == 14
    assert report.selected_correct_by_group == (
        2, 2, 2, 2, 2, 2, 2, 2, 1, 0, 1, 2, 2, 2, 1, 2, 2, 2)
    assert report.rollout_descriptor_digest == \
        "bd9d0877bb9f7af16a3c8134a76f474e77e3c8d423a67cc6d7a54dcb34593a97"
    assert min(report.evaluated_child_branches_by_group) >= 76
    assert report.rollout_constructed_target_free
    assert not report.exact_candidate_geometry_changed
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("two-step successor IQC value regression passed")


if __name__ == "__main__":
    main()
