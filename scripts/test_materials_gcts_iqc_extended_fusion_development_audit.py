#!/usr/bin/env python3

from materials_gcts_iqc_extended_fusion_development_audit import evaluate


def test_extended_fusion_transfers_but_does_not_improve_scalar_or_supply():
    report = evaluate()
    assert report.nuclei == 10
    assert report.selected_sites == 30
    assert report.scalar_terminal_supply == 6
    assert report.fusion_terminal_supply == 6
    assert report.scalar_selected_exact == report.fusion_selected_exact == 6
    assert report.scalar_selected_correct == \
        report.fusion_selected_correct == 23
    assert report.exact_candidate_missing_nuclei == 4
    assert report.fusion_changed_selected_terminal_nuclei == 5
    assert report.fusion_changed_outcome_nuclei == 0
    assert report.bound_plus_one_stable
    assert report.pairwise_disjoint
    assert report.target_open_count == 1
    assert not report.target_used_before_scoring
    assert report.development_transfer_gate_passed
    assert not report.incremental_fusion_advantage
    assert not report.candidate_supply_gate_passed
    assert not report.stationary_or_exponential_claimed


if __name__ == "__main__":
    test_extended_fusion_transfers_but_does_not_improve_scalar_or_supply()
    print("extended IQC fusion development-audit tests passed")
