#!/usr/bin/env python3
"""Regression for the width-16 directed IQC obligation search."""

from materials_gcts_iqc_path_conditioned_successor_audit import evaluate


def main():
    report = evaluate(16)
    assert report.path_branching == 16
    assert report.selected_correct_actions == 33
    assert report.selected_false_actions == 3
    assert report.exact_groups == 16
    assert report.selected_correct_by_group == (
        2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2)
    assert report.path_descriptor_digest == \
        "ced0451db9074a160ca3bc2c30624e14e188d89c971b92d72e51cac5379c3b53"
    assert report.heldout_exact_paths_by_group[1] == 4
    assert report.heldout_exact_paths_by_group[0] == 0
    assert report.heldout_exact_paths_by_group[14] == 0
    assert report.path_descriptors_constructed_before_labels
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("wide path-conditioned IQC successor regression passed")


if __name__ == "__main__":
    main()
