#!/usr/bin/env python3

from materials_gcts_iqc_pose_port_state_audit import evaluate


def test_pose_port_quotient_passes_conditional_development_gate():
    report = evaluate()
    assert report.training_groups == 10
    assert report.validation_groups == 8
    assert report.training_candidates == 20716
    assert report.training_exact_actions == 1151
    assert report.upstream_angular_bin_width == .125
    assert not report.pose_atlas_refit_during_marking
    assert report.selected_state_bin_width == 1.
    assert report.selected_token_setting == (4, 2)
    assert report.selected_training_exact_stages == 18
    assert report.eligible_training_stages == 28
    assert report.channel_families
    assert len(report.channel_families) == 5
    assert report.frozen_recurrent_states == 437
    assert report.frozen_state_marking_digest == \
        "9b83898155f5d729499c441bcbafa6491b553196fe87de756cb6281b8b856b13"
    assert report.candidate_digest == \
        "a241b449374deadd73ff32fc48f45c87412e0fa8073c6fac35848e5bc5e785b4"
    assert report.state_top1_exact_groups == 8
    assert report.state_first_exact_ranks == (1,) * 8
    assert report.state_required_beam_width == 1
    assert report.finite_pose_port_quotient_improves_selection
    assert report.conditional_top1_gate_passed
    assert not report.exact_candidate_geometry_changed
    assert report.proper_rotation_quotiented
    assert not report.raw_rotation_count_used_as_channel_count
    assert not report.heldout_truth_used_to_select_quotient
    assert report.validation_truth_used_to_construct_conditional_prefix
    assert not report.autonomous_growth_claimed


if __name__ == "__main__":
    test_pose_port_quotient_passes_conditional_development_gate()
    print("IQC pose-port state audit passed")
