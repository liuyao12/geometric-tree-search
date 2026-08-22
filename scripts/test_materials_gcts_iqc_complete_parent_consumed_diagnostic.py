#!/usr/bin/env python3
"""Regression loader for the consumed complete-parent diagnosis."""

from materials_gcts_iqc_complete_parent_consumed_diagnostic import (
    load_default_result)


def test_failure_is_localized_without_revising_fresh_claim() -> None:
    row = load_default_result()
    assert row["complete_parent_antichain"]
    assert set(row["complete_selected_parent_ids"]) == set(range(1, 9))
    assert row["diagnostic_parent_id"] == 2
    assert not row["diagnostic_parent_originally_selected"]
    assert row["diagnostic_parent_exact_first_actions"] == 3
    assert row["diagnostic_exact_second_children"] == [98, 99, 100, 120]
    assert row["diagnostic_child_id"] == 120
    assert row["diagnostic_child_retained_target_free"]
    assert row["third_candidate_counts"] == [8, 38, 142]
    assert row["third_lineages"] == 142
    assert row["best_correct_actions"] == 9
    assert row["exact_nine_action_lineages"] == 18
    assert row["failure_localized_to_four_parent_truncation"]
    assert not row["candidate_selection_target_used"]
    assert row["diagnostic_branch_chosen_posthoc"]
    assert row["consumed_target_diagnostic_only"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["winner_or_autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_failure_is_localized_without_revising_fresh_claim()
    print("complete-parent consumed diagnosis: passed")
