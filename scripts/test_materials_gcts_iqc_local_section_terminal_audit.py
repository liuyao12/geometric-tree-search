#!/usr/bin/env python3

from materials_gcts_iqc_local_section_terminal_audit import evaluate


def test_port_fusion_passes_development_but_not_causal_gate():
    report = evaluate()
    assert report.groups == 20
    assert report.features == 180
    assert report.terminal_supply == 18
    assert report.baseline_selected_exact == 16
    assert report.selected_exact == 17
    assert report.selected_correct == 55
    assert report.gain_over_baseline == 1
    assert report.joint_support_selected_exact == 17
    assert report.closure_selected_folds == 0
    assert report.irregular_support_types == 53
    assert report.irregular_support_selected_folds == 2
    assert report.irregular_selected_exact == 17
    assert report.irregular_selected_correct == 55
    assert report.irregular_incidence_selected_folds == 2
    assert report.irregular_incidence_selected_exact == 17
    assert report.irregular_incidence_selected_correct == 54
    assert report.typed_port_graph_selected_folds == 0
    assert report.typed_port_graph_best_inner_exact == 24
    assert report.graph_kernel_selected_folds == 2
    assert report.graph_kernel_best_inner_exact == 25
    assert report.graph_kernel_selected_exact == 17
    assert report.graph_kernel_selected_correct == 54
    assert report.message_passing_selected_folds == 0
    assert report.message_passing_best_inner_exact == 24
    assert report.message_passing_selected_exact == 17
    assert report.message_passing_selected_correct == 54
    assert report.learned_message_selected_folds == 2
    assert report.learned_message_best_inner_exact == 26
    assert report.learned_message_standalone_exact == 15
    assert report.learned_message_integrated_exact == 16
    assert report.learned_message_integrated_correct == 54
    assert report.learned_message_exact_shuffle_p == .375
    assert report.equivariant_fusion_selected_folds == 3
    assert report.equivariant_fusion_selected_exact == 18
    assert report.equivariant_fusion_selected_correct == 56
    assert report.equivariant_fusion_exact_shuffle_p == .09375
    assert not report.equivariant_fusion_causal_gate_passed
    assert report.chiral_features == 210
    assert report.chirality_selected_folds == 2
    assert report.chiral_selected_exact == 15
    assert report.chiral_selected_correct == 55
    assert report.proper_se3_invariant
    assert not report.lattice_coordinates_used
    assert not report.chirality_preserved
    assert report.development_gate_passed
    assert not report.fresh_confirmation_authorized
    assert not report.target_used


if __name__ == "__main__":
    test_port_fusion_passes_development_but_not_causal_gate()
    print("IQC local-section terminal audit passed")
