#!/usr/bin/env python3
"""Pinned positive fallback evidence for the bounded hybrid prefix policy."""

from materials_gcts_iqc_hybrid_prefix_third_supply_benchmark import \
    load_default_result


def test_bounded_hybrid_supplies_joint_and_fallback_exact_lineages():
    row = load_default_result()
    assert row["selected_prefixes"] == 12
    assert row["joint_prefixes"] == 8
    assert row["diverse_fallback_prefixes"] == 4
    assert row["raw_nine_action_lineages"] == 1640
    assert row["exact_nine_action_lineages"] == 6
    assert row["joint_exact_lineages"] == 3
    assert row["fallback_exact_lineages"] == 3
    assert row["exact_prefixes"] == [[8, 89], [8, 123]]
    assert [8, 123] in row["fallback_prefixes"]
    assert row["best_correct_actions"] == 9
    assert not row["candidate_selection_target_used"]
    assert not row["fresh_confirmation_claimed"]


if __name__ == "__main__":
    test_bounded_hybrid_supplies_joint_and_fallback_exact_lineages()
    print("IQC bounded hybrid third-supply tests passed")
