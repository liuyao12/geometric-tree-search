#!/usr/bin/env python3
"""Regression for post-commit IQC orientation-channel selection."""

from materials_gcts_iqc_postcommit_orientation_channel_audit import evaluate


def test_postcommit_orientation_capacity_is_not_mistaken_for_transfer():
    report = evaluate()
    assert report.training_candidates == 20_716
    assert report.training_exact_actions == 1_151
    assert report.selected_angular_bin_width == .125
    assert report.selected_score_mode == "channel"
    assert report.selected_training_exact_stages == 23
    assert report.eligible_training_stages == 28
    assert report.frozen_oriented_tokens == 28_558
    assert report.oriented_first_exact_ranks == (5, 1, 7, 6, 1, 3, 3, 3)
    assert report.oriented_top1_exact_by_group == (
        False, True, False, False, True, False, False, False)
    assert report.oriented_top1_exact_groups == 2
    assert report.oriented_required_beam_width == 7
    assert report.unoriented_first_exact_ranks == (3, 4, 3, 3, 1, 1, 1, 1)
    assert report.unoriented_top1_exact_groups == 4
    assert not report.orientation_improves_heldout_selection
    assert not report.exact_candidate_geometry_changed
    assert report.proper_rotation_quotiented
    assert report.chirality_preserved
    assert not report.orientation_capacity_transfer_gate_passed
    assert not report.heldout_truth_used_to_select_orientation
    assert report.validation_truth_used_to_construct_conditional_prefix
    assert not report.autonomous_growth_claimed


if __name__ == "__main__":
    test_postcommit_orientation_capacity_is_not_mistaken_for_transfer()
    print("post-commit IQC orientation-channel audit passed")
