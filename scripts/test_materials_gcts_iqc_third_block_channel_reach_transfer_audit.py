#!/usr/bin/env python3

from materials_gcts_iqc_third_block_channel_reach_transfer_audit import (
    load_default_result)


def test_compute_matched_channel_reach_preserves_consumed_transfer_groups():
    row = load_default_result()
    assert row["exact_parents"] == 15
    assert row["design_parents_reused"] == 4
    assert row["generated_transfer_parents"] == 11
    assert row["action_budget"] == 8
    assert row["matched_child_expansion_budget"]
    assert row["baseline_supplied_parents"] == 11
    assert row["channel_supplied_parents"] == 15
    assert row["baseline_supplied_groups"] == 6
    assert row["channel_supplied_groups"] == 8
    assert row["baseline_exact_paths"] == 90
    assert row["channel_exact_paths"] == 472
    assert row["baseline_supplied_group_ids"] == [0, 4, 6, 7, 8, 9]
    assert row["channel_supplied_group_ids"] == [0, 1, 2, 4, 6, 7, 8, 9]
    assert row["baseline_transfer_groups_preserved"]
    assert row["design_groups_recovered"]
    assert row["development_preservation_gate_passed"]
    assert row["target_open_count"] == 1
    assert not row["target_used_for_candidate_generation_or_ranking"]
    assert row["selector_proposed_after_consumed_failure"]
    assert row["consumed_development_only"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["causal_superiority_claimed"]
    assert not row["autonomous_commit_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_compute_matched_channel_reach_preserves_consumed_transfer_groups()
    print("IQC channel-reach transfer audit: passed")
