#!/usr/bin/env python3
"""Regression for the width-16 directed IQC obligation search."""

from materials_gcts_iqc_path_conditioned_successor_audit import evaluate


def main():
    report = evaluate(16)
    assert report.path_branching == 16
    assert report.selected_correct_actions == 34
    assert report.selected_false_actions == 2
    assert report.exact_groups == 16
    assert report.selected_correct_by_group == (
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2)
    assert report.path_descriptor_digest == \
        "f1fc39d0f8a23d8e00b3089c2e7536c84c61cb7780ccb4e8fe3eaddd251e3534"
    assert min(report.heldout_exact_paths_by_group) >= 2
    assert report.path_descriptors_constructed_before_labels
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("wide path-conditioned IQC successor regression passed")


if __name__ == "__main__":
    main()
