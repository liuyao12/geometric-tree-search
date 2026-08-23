#!/usr/bin/env python3
"""Development-only regression for action-marginal fallback supply."""

from materials_gcts_iqc_action_marginal_prefix_audit import \
    evaluate, validate_result


def test_structural_fallback_preserves_all_known_exact_prefix_groups():
    row = validate_result(evaluate())
    assert row["exact_child_groups"] == 6
    assert row["joint_supplied_exact_groups"] == 6
    assert row["augmented_supplied_exact_groups"] == 6
    assert row["selected_prefixes_across_cases"] == 64
    assert row["fallback_prefixes_across_cases"] == 32
    assert not row["candidate_selection_target_used"]


if __name__ == "__main__":
    test_structural_fallback_preserves_all_known_exact_prefix_groups()
    print("IQC action-marginal prefix audit tests passed")
