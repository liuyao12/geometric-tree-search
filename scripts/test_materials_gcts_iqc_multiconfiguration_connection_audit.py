#!/usr/bin/env python3
"""Regression for raw multi-configuration IQC connection supply."""

from materials_gcts_iqc_multiconfiguration_connection_audit import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.selected_spec.minimum_positive_groups == 2
    assert report.selected_groups_with_correct_candidates == 14
    assert report.selected_groups_with_exact_path == 7
    selected = report.audits[0]
    assert selected.correct_candidate_actions_by_group == (
        0, 4, 5, 36, 37, 37, 37, 37, 3, 0, 6, 2, 0, 0, 4, 24, 24, 24)
    assert selected.exact_path_available_by_group == (
        False, False, False, False, True, True, True, True, False, False,
        False, False, False, False, False, True, True, True)
    assert report.connection_learning_uses_training_targets
    assert not report.heldout_target_used_for_connection_fit_or_proposals
    assert report.heldout_truth_opened_only_for_supply_scoring
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.supply_gate_passed
    print("multi-configuration IQC connection regression passed")


if __name__ == "__main__":
    main()
