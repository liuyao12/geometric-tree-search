#!/usr/bin/env python3

from materials_gcts_iqc_third_block_channel_reach_audit import (
    load_default_result)


def test_compute_matched_channel_reach_on_consumed_failures():
    row = load_default_result()
    assert row["parents_scored"] == 4
    assert row["action_budget"] == 8
    assert row["baseline_slots"] == 3
    assert row["channel_slots"] == 5
    assert row["matched_child_expansion_budget"]
    assert row["baseline_supplied_parents"] == 0
    assert row["supplied_parents"] == 4
    assert row["supplied_groups"] == 2
    assert [parent["exact_terminal_paths"]
            for parent in row["scored_parents"]] == [11, 10, 11, 10]
    assert [parent["candidate_counts_by_depth"]
            for parent in row["receipt"]] == [
                [8, 37, 131], [8, 37, 129],
                [8, 37, 131], [8, 37, 129]]
    assert row["target_open_count"] == 1
    assert not row["target_used_for_parent_replay_or_candidate_selection"]
    assert row["selector_proposed_after_consumed_failure"]
    assert row["consumed_development_only"]
    assert not row["causal_superiority_claimed"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_commit_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_compute_matched_channel_reach_on_consumed_failures()
    print("IQC compute-matched channel reach audit: passed")
