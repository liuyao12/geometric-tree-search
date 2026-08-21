#!/usr/bin/env python3
"""Preserve the consumed red rollout-ranked IQC confirmation."""

from materials_gcts_iqc_stage_local_rollout_confirmation import (
    EXPECTED_RESULT_DIGEST, load_receipt)


def test_consumed_rollout_confirmation_remains_red_without_leakage() -> None:
    row = load_receipt()
    assert row["result_digest"] == EXPECTED_RESULT_DIGEST
    assert row["confirmation_center"] == [120.0, -40.0, -220.0]
    assert row["seed_atoms"] == 476
    assert row["target_atoms"] == 2069
    assert row["identical_first_block_candidate_work"]
    assert row["target_open_count"] == 1
    assert row["target_opened_after_all_traces_froze"]
    assert not row["target_used_for_candidate_ranking_or_execution"]
    assert row["marked_score"]["correct_sites"] == 6
    assert row["marked_score"]["wrong_sites"] == 3
    assert row["marked_score"]["exact_blocks"] == 0
    assert row["baseline_score"]["correct_sites"] == 6
    assert row["baseline_score"]["wrong_sites"] == 3
    assert row["baseline_score"]["exact_blocks"] == 1
    assert [block["selected_index"] for block in
            row["marked_trace"]["blocks"]] == [7, 5, 4]
    assert [block["selected_index"] for block in
            row["baseline_trace"]["blocks"]] == [0, 0, 0]
    assert not row["first_block_transfer_gate_passed"]
    assert not row["sustained_three_block_gate_passed"]
    assert not row["autonomous_finite_continuation_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_consumed_rollout_confirmation_remains_red_without_leakage()
    print("red stage-local rollout confirmation receipt preserved")
