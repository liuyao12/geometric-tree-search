#!/usr/bin/env python3
"""Regression for finite conditional states on expanded IQC development."""

from materials_gcts_iqc_expanded_state_quotient import evaluate


def test_conditional_states_remain_below_expanded_gate():
    report = evaluate()
    assert report.total_groups == 18
    assert report.selected_spec.minimum_support == 4
    assert report.selected_spec.minimum_groups == 2
    assert report.selected_correct_by_group == \
        (2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 1, 1, 2, 2, 2, 1, 1, 1)
    assert report.selected_actions == 36
    assert report.selected_correct_actions == 29
    assert report.selected_false_actions == 7
    assert report.exact_groups == 12
    selected = next(row for row in report.audits
                    if row.spec == report.selected_spec)
    assert selected.supported_states_by_fold_and_level[0] == \
        (4498, 4636, 2337, 1404)
    assert selected.supported_states_by_fold_and_level[-1] == \
        (4353, 4433, 2255, 1352)
    assert selected.fold_model_digest == \
        "45d5f572af7522a7dd93412f1ef82910b3723dcb82b99122115c2f0aa4118fa5"
    assert report.exact_candidate_geometry_changed is False
    assert report.expanded_targets_used_for_development_fit is True
    assert report.next_confirmation_seed_or_target_accessed is False
    assert report.development_gate_passed is False


def main():
    test_conditional_states_remain_below_expanded_gate()
    print("expanded IQC conditional-state regression passed")


if __name__ == "__main__":
    main()
