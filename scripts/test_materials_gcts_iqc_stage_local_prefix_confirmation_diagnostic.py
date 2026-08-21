#!/usr/bin/env python3
"""Regression for the consumed stage-local confirmation diagnosis."""

from materials_gcts_iqc_stage_local_prefix_confirmation_diagnostic import (
    EXPECTED_DIAGNOSTIC_DIGEST, evaluate)


def test_confirmation_failed_on_a_saturated_depth_one_tie():
    row = evaluate()
    assert row["diagnostic_digest"] == EXPECTED_DIAGNOSTIC_DIGEST
    assert row["candidate_counts_by_depth"] == (12, 38, 152)
    assert row["complete_exact_terminal_count"] == 6
    assert row["selected_terminal_reproduces_confirmation"]
    assert row["first_depth_without_retained_viable_prefix"] == 1
    first = row["stages"][0]
    assert first["all_viable"] == 5
    assert first["first_viable_rank"] == 3
    assert first["selected_viable"] == 0
    assert tuple(item["score"] for item in first["selected"]) == (1., 1.)
    assert first["best_viable"]["score"] == 1.
    assert row["stages"][1]["eligible_viable"] == 0
    assert row["stages"][2]["eligible_viable"] == 0
    assert row["target_opened_only_after_complete_geometry"]
    assert row["consumed_posthoc_diagnostic"]
    assert not row["retry_authorized"]
    assert not row["policy_integrated"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_confirmation_failed_on_a_saturated_depth_one_tie()
    print("stage-local confirmation failure diagnosis preserved")
