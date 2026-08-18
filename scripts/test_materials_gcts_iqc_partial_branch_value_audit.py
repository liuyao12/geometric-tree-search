#!/usr/bin/env python3

from materials_gcts_iqc_partial_branch_value_audit import evaluate


def test_depth_conditioned_value_passes_snapshots_but_not_closed_loop():
    report = evaluate()
    assert report.groups == 30
    assert report.stages == 90
    assert report.examples == 1259
    assert report.positive_examples == 934
    assert report.search_schedule == (4, 4, 8)
    assert report.selected_neighbors_by_depth == ((1, 25), (2, 15), (3, 9))
    assert report.supplied_stages_by_depth == (29, 28, 28)
    assert report.selected_exact_stages_by_depth == (29, 27, 25)
    assert report.supplied_stages == 85
    assert report.selected_exact_stages == 81
    assert report.selected_precision == 81 / 85
    assert report.candidate_digest_matches
    assert report.model_digest_matches
    assert report.frozen_snapshot_gate_passed
    assert report.consumed_closed_loop_beam_widths == (4, 8, 16)
    assert report.consumed_closed_loop_exact_terminals == (0, 0, 0)
    assert report.consumed_closed_loop_selected_correct_sites == (2, 2, 2)
    assert report.consumed_target_reopened_only_after_confirmation
    assert not report.autonomous_closed_loop_gate_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_depth_conditioned_value_passes_snapshots_but_not_closed_loop()
    print("IQC partial branch value audit passed")
