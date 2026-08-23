#!/usr/bin/env python3
"""Development-only regression for action-marginal fallback supply."""

from materials_gcts_iqc_action_marginal_prefix_audit import \
    evaluate, evaluate_compute_bounded, validate_result


def test_structural_fallback_preserves_all_known_exact_prefix_groups():
    row = validate_result(evaluate())
    assert row["exact_child_groups"] == 6
    assert row["joint_supplied_exact_groups"] == 6
    assert row["augmented_supplied_exact_groups"] == 6
    assert row["selected_prefixes_across_cases"] == 64
    assert row["fallback_prefixes_across_cases"] == 32
    assert not row["candidate_selection_target_used"]


def test_compute_bounded_policy_preserves_groups_with_ten_prefix_mean():
    row = validate_result(evaluate_compute_bounded())
    assert row["exact_child_groups"] == 6
    assert row["augmented_supplied_exact_groups"] == 6
    assert row["selected_prefixes_across_cases"] == 44
    assert row["fallback_prefixes_across_cases"] == 12
    assert row["maximum_fallbacks_per_case"] == 4
    assert row["universal_avoidance_required"]
    assert row["base_tail_when_unsaturated"]


if __name__ == "__main__":
    test_structural_fallback_preserves_all_known_exact_prefix_groups()
    test_compute_bounded_policy_preserves_groups_with_ten_prefix_mean()
    print("IQC action-marginal prefix audit tests passed")
