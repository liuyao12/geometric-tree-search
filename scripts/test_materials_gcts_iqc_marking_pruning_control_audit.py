#!/usr/bin/env python3

from materials_gcts_iqc_marking_pruning_control_audit import evaluate


def test_pruning_controls_are_preserved_as_honest_negative_results():
    report = evaluate()
    assert report.groups == 20
    assert report.beam == (4, 4, 8)
    assert report.baseline_selected_exact == 16
    assert report.baseline_terminal_supply == 18
    assert report.reach12_root_supply == 20
    assert report.reach12_terminal_supply == 17
    assert report.reach12_selected_exact == 13
    assert report.stage_value_selected_exact == 16
    assert report.stage_value_terminal_supply == 17
    assert report.descendant_viability_selected_exact == 15
    assert report.descendant_viability_terminal_supply == 16
    assert report.lookahead_terminal_supply == 20
    assert report.lookahead_selected_exact == 12
    assert report.lookahead_proposal_checks == 7312
    assert report.pose_edge_selected_exact == 15
    assert report.pose_edge_selected_correct == 54
    assert report.pose_edge_representation_selected_folds == 0
    assert not report.controls_improve_baseline
    assert not report.development_gate_passed
    assert not report.fresh_confirmation_authorized
    assert not report.target_used


if __name__ == "__main__":
    test_pruning_controls_are_preserved_as_honest_negative_results()
    print("IQC marking pruning controls passed")
