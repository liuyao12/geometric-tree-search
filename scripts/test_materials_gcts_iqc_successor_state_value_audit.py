#!/usr/bin/env python3
"""Regression for target-free successor-state value on expanded IQC data."""

from materials_gcts_iqc_successor_state_value_audit import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.shortlist_size == 16
    assert report.additive_baseline_correct_actions == 30
    assert report.selected_correct_actions == 32
    assert report.selected_false_actions == 4
    assert report.exact_groups == 15
    assert report.selected_correct_by_group == (
        2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 1, 2, 2, 2, 1, 2, 2, 2)
    assert report.successor_descriptor_digest == \
        "315e088505ff03aadb12d2c5c78cb9f2cfd0815357113bd6dcb8cf6ead81870d"
    assert min(report.unique_successors_by_group) >= 19
    assert all(low <= high for low, high in zip(
        report.outgoing_minimum_by_group, report.outgoing_maximum_by_group))
    assert report.successor_constructed_target_free
    assert not report.exact_candidate_geometry_changed
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("successor-state IQC value regression passed")


if __name__ == "__main__":
    main()
