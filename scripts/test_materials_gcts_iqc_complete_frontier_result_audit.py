#!/usr/bin/env python3

from materials_gcts_iqc_complete_frontier_result_audit import evaluate


def test_widened_tree_fixes_supply_but_not_top_one_selection():
    report = evaluate()
    assert report.nuclei == 10
    assert report.baseline_supply == report.final_only_supply == \
        report.second_depth_supply == 6
    assert report.complete_frozen_reach_supply == 9
    assert report.widened_supply == 10
    assert report.minimum_dual_budget == 9
    assert report.maximum_dual_states == 18
    assert report.fusion_top_one_exact == 6
    assert report.candidate_supply_gate_passed
    assert not report.top_one_selection_gate_passed
    assert not report.fresh_confirmation_claimed
    assert not report.stationary_or_exponential_claimed


if __name__ == "__main__":
    test_widened_tree_fixes_supply_but_not_top_one_selection()
    print("complete IQC frontier result-audit tests passed")
