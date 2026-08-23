#!/usr/bin/env python3
"""Pinned development evidence for the V4 third-prefix stage."""

from materials_gcts_iqc_action_marginal_third_supply_benchmark import \
    load_default_result


def test_joint_and_fallback_lineage_supply_is_pinned_honestly():
    row = load_default_result()
    assert row["selected_prefixes"] == 16
    assert row["raw_nine_action_lineages"] == 2162
    assert row["exact_nine_action_lineages"] == 3
    assert row["joint_exact_lineages"] == 3
    assert row["fallback_exact_lineages"] == 0
    assert row["best_correct_actions"] == 9
    assert not row["candidate_selection_target_used"]
    assert not row["fresh_confirmation_claimed"]


if __name__ == "__main__":
    test_joint_and_fallback_lineage_supply_is_pinned_honestly()
    print("IQC action-marginal third-supply tests passed")
