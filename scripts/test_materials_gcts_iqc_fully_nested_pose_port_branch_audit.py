#!/usr/bin/env python3

from materials_gcts_iqc_fully_nested_pose_port_branch_audit import evaluate


def test_real_fully_nested_pose_port_branch_audit_is_honestly_red():
    report = evaluate()
    assert report.groups == 20
    assert report.folds == 5
    assert report.broad_examples == 5574
    assert report.on_policy_examples == 4467
    assert report.conflicting_descriptor_groups == 5
    assert report.feature_count == 31
    assert report.pose_port_channels_per_action == 5
    assert report.maximum_actions == 3
    assert (report.base_selected_exact, report.base_terminal_supply) == (14, 17)
    assert (report.colored_geometry_selected_exact,
            report.colored_geometry_terminal_supply) == (15, 17)
    assert (report.pose_port_only_selected_exact,
            report.pose_port_only_terminal_supply) == (14, 16)
    assert (report.coupled_selected_exact,
            report.coupled_terminal_supply) == (15, 16)
    assert report.aggregated_selected_exact == 14
    assert report.aggregated_terminal_supply == 16
    assert report.aggregated_selected_correct_moves == 52
    assert not report.raw_pose_port_channels_improve_base
    assert report.colored_geometry_improves_base
    assert report.coupled_representation_improves_base
    assert not report.on_policy_aggregation_improves_coupled_model
    assert report.broad_upstream_pose_port_fully_nested
    assert report.on_policy_upstream_pose_port_fully_nested
    assert not report.scientific_gate_passed
    assert not report.fresh_confirmation_authorized
    assert report.corpus_digest == \
        "8ebfa3e6cc445fd84d33089ef92c96dbe238108dc6958a73ef6e929953e7d0e3"
    assert report.closed_loop_candidate_digest == \
        "3658d67adddd8f92d07471e5681b6ce60583861bbbf655a3ed84cb0bf76871af"
    assert not report.target_used


if __name__ == "__main__":
    test_real_fully_nested_pose_port_branch_audit_is_honestly_red()
    print("fully nested IQC pose-port branch audit passed")
