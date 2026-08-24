#!/usr/bin/env python3
"""Pinned honest result of the two-fallback fresh IQC confirmation."""

from collections import Counter

from materials_gcts_iqc_hybrid_confirmation_v4 import load_default_result


def test_fresh_hybrid_result_is_runtime_green_but_scientifically_red():
    row = load_default_result()
    assert row["raw_nine_action_lineages"] == 1254
    assert row["raw_exact_nine_action_lineages"] == 0
    assert row["selected_exact_nine_action_lineages"] == 0
    assert row["exact_terminal_fourth_blocks"] == 208
    assert row["exact_complete_twelve_action_paths"] == 0
    assert row["best_complete_correct_actions"] == 7
    assert row["runtime_gate_passed"]
    assert row["total_execution_seconds"] == 434.041247125
    assert not row["fresh_exact_twelve_action_supply_confirmed"]


def test_failure_is_upstream_of_exact_third_and_fourth_blocks():
    row = load_default_result()
    raw = row["raw_nine_action_labels"]
    complete = row["candidate_action_labels"]
    assert [sum(all(values[start:start + 3]) for values in raw)
            for start in (0, 3, 6)] == [0, 0, 377]
    assert [max(sum(values[start:start + 3]) for values in raw)
            for start in (0, 3, 6)] == [1, 1, 3]
    assert [sum(all(values[start:start + 3]) for values in complete)
            for start in (0, 3, 6, 9)] == [0, 0, 160, 208]
    assert Counter(map(sum, complete)) == {
        3: 48, 4: 169, 5: 95, 6: 40, 7: 160}


def test_fresh_result_is_disjoint_and_receipt_is_immutable():
    row = load_default_result()
    audit = row["target_order_audit"]
    assert row["nearest_prior_center_separation"] > \
        row["required_domain_separation"]
    assert row["receipt_serialized_before_target"]
    assert row["receipt_unchanged_after_target"]
    assert not row["target_used_for_generation_fit_or_ranking"]
    assert audit["seed_open_count"] == audit["target_open_count"] == 1
    assert audit["score_count"] == 1


if __name__ == "__main__":
    test_fresh_hybrid_result_is_runtime_green_but_scientifically_red()
    test_failure_is_upstream_of_exact_third_and_fourth_blocks()
    test_fresh_result_is_disjoint_and_receipt_is_immutable()
    print("V4 fresh hybrid IQC confirmation tests passed")
