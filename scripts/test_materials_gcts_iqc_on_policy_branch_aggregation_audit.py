#!/usr/bin/env python3

from materials_gcts_iqc_on_policy_branch_aggregation_audit import evaluate


def test_real_iqc_on_policy_aggregation_is_improved_but_still_red():
    report = evaluate()
    assert report.groups == 20
    assert report.folds == 5
    assert report.on_policy_examples == 4037
    assert report.positive_on_policy_examples == 3224
    assert report.conflicting_descriptor_groups == 15
    assert report.initial_terminal_supply == 16
    assert report.initial_selected_exact == 10
    assert report.initial_selected_correct_sites == 44
    assert report.aggregated_stage_supply == (19, 18, 18)
    assert report.aggregated_terminal_supply == 18
    assert report.aggregated_selected_exact == 13
    assert report.aggregated_selected_correct_sites == 51
    assert report.exact_path_supply_failures == 2
    assert report.supplied_but_misranked == 5
    assert report.terminal_supply_fraction == .9
    assert report.selected_exact_fraction == .65
    assert report.improvement_over_initial == 3
    assert report.terminal_supply_gate_passed
    assert not report.selected_exact_gate_passed
    assert report.improvement_gate_passed
    assert not report.development_gate_passed
    assert not report.fresh_confirmation_authorized
    assert report.on_policy_corpus_digest == \
        "3683f5091e954c0605fa0115193365a9210a26074e61f1ee539cbbd12831d53f"
    assert report.closed_loop_candidate_digest == \
        "395eba0f5a5e66a43a4367cb5e447d48082c67aed60497c9a5631791e5d76cbd"
    assert not report.target_used


if __name__ == "__main__":
    test_real_iqc_on_policy_aggregation_is_improved_but_still_red()
    print("IQC on-policy branch aggregation audit passed")
