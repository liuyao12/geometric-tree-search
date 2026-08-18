#!/usr/bin/env python3
"""Regression for proper-rotation-invariant IQC port orientation channels."""

from materials_gcts_iqc_oriented_port_channel_audit import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.selected_angular_bin_width == .5
    assert report.selected_score_mode == "additive"
    assert report.selected_correct_actions == 30
    assert report.selected_false_actions == 6
    assert report.exact_groups == 14
    assert report.unoriented_baseline_correct_actions == 30
    assert tuple(row.orientation_tokens for row in report.audits[::2]) == (
        9580, 6501, 4414)
    assert report.proper_rotation_quotiented
    assert report.chirality_preserved
    assert not report.exact_candidate_geometry_changed
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("oriented-port IQC channel regression passed")


if __name__ == "__main__":
    main()
