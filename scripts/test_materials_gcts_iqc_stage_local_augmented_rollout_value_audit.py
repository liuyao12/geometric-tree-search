#!/usr/bin/env python3
"""Regression for the augmented stage-local IQC rollout-value gate."""

from materials_gcts_iqc_stage_local_augmented_rollout_value_audit import (
    EXPECTED_AUDIT_DIGEST, evaluate)


def test_augmented_rollout_value_beats_connection_and_shuffle_controls() -> None:
    row = evaluate()
    assert row["audit_digest"] == EXPECTED_AUDIT_DIGEST
    assert row["training_candidates"] == 320
    assert row["execution_candidates"] == 160
    assert row["exact_execution_supply_groups"] == 19
    assert row["selected_model"]["model_id"] == "temporal-61"
    assert row["selected_result"]["exact"] == 19
    assert row["selected_result"]["sites"] == 59
    assert row["connection_top_one_exact"] == 19
    assert row["connection_top_one_sites"] == 57
    assert row["selected_result"]["exact"] > row["shuffle_exact_maximum"]
    assert row["selected_result"]["sites"] > row["shuffle_sites_maximum"]
    assert row["shuffle_exact_upper_tail_p"] == .03125
    assert row["shuffle_sites_upper_tail_p"] == .03125
    assert row["candidate_label_vectors_shuffled_over_all_sixteen"]
    assert not row["quantile_training_candidates_used_at_execution"]
    assert not row["targets_used_for_receipts_or_ranking"]
    assert not row["fresh_confirmation_opened"]
    assert row["augmented_rollout_gate_passed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_augmented_rollout_value_beats_connection_and_shuffle_controls()
    print("augmented stage-local rollout value gate passed")
