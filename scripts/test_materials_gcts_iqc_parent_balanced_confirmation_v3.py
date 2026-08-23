#!/usr/bin/env python3
"""Pinned honest result of the third fresh full-width IQC confirmation."""

from materials_gcts_iqc_parent_balanced_confirmation_v3 import \
    load_default_result


def test_fresh_result_localizes_failure_to_raw_parent_supply():
    row = load_default_result()
    assert row["raw_nine_action_lineages"] == 1087
    assert row["raw_exact_nine_action_lineages"] == 0
    assert row["selected_exact_nine_action_lineages"] == 0
    assert row["fourth_candidates"] == 512
    assert row["exact_terminal_fourth_blocks"] == 197
    assert row["exact_complete_twelve_action_paths"] == 0
    assert row["best_complete_correct_actions"] == 11
    assert not row["fresh_exact_twelve_action_supply_confirmed"]


def test_fresh_result_is_disjoint_one_shot_and_runtime_green():
    row = load_default_result()
    audit = row["target_order_audit"]
    assert row["nearest_prior_center_separation"] > \
        row["required_domain_separation"]
    assert row["receipt_serialized_before_target"]
    assert row["receipt_unchanged_after_target"]
    assert not row["target_used_for_generation_fit_or_ranking"]
    assert audit["seed_open_count"] == audit["target_open_count"] == 1
    assert audit["score_count"] == 1
    assert row["runtime_gate_passed"]
    assert row["total_execution_seconds"] == 534.838081083


def test_all_best_paths_share_one_upstream_false_action():
    row = load_default_result()
    labels = row["candidate_action_labels"]
    candidates = row["receipt"]["candidates"]
    best = max(sum(values) for values in labels)
    best_rows = tuple((candidate, values) for candidate, values in
                      zip(candidates, labels) if sum(values) == best)
    assert len(best_rows) == 6
    failures = {
        (tuple(candidate["all_actions"][index][0]),
         candidate["all_actions"][index][1])
        for candidate, values in best_rows
        for index, correct in enumerate(values) if not correct
    }
    assert failures == {
        ((-190.532889, -78.63119, -303.052622), "Y")}


if __name__ == "__main__":
    test_fresh_result_localizes_failure_to_raw_parent_supply()
    test_fresh_result_is_disjoint_one_shot_and_runtime_green()
    test_all_best_paths_share_one_upstream_false_action()
    print("V3 fresh parent-balanced confirmation tests passed")
