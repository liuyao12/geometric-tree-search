#!/usr/bin/env python3
"""Regression for tie-robust stage-local marking selection."""

from materials_gcts_iqc_stage_local_margin_marking_audit import (
    EXPECTED_AUDIT_DIGEST, evaluate)


def test_margin_selection_prefers_the_existing_nonsaturated_model():
    row = evaluate()
    selected = row["selected_result"]
    assert row["audit_digest"] == EXPECTED_AUDIT_DIGEST
    assert row["old_confirmation_imported_or_used"] is False
    assert row["selection_adds_margin_tie_and_resolution_after_exact_yield"]
    assert selected["budget"] == (4, 8, 1)
    assert tuple(stage["spec"] for stage in selected["stages"]) == (
        {"variant": "coupled", "neighbors": 19, "weighted": True},
        {"variant": "section", "neighbors": 19, "weighted": True},
        {"variant": "coupled", "neighbors": 19, "weighted": True},
    )
    first = selected["stages"][0]
    assert first["viable_groups"] == 20
    assert first["tie_safe_groups"] == 20
    assert first["minimum_class_margin"] > .12
    assert first["minimum_score_resolution"] >= 6
    assert selected["exact_selected_groups"] == 19
    assert row["matched_pose_port_baseline"]["exact_selected_groups"] == 1
    assert row["shuffle_exact_group_maximum"] == 11
    assert row["shuffle_group_upper_tail_p"] == 1 / 32
    assert row["shuffle_row_upper_tail_p"] == 1 / 32
    assert row["tie_robust_stage_local_gate_passed"]
    assert not row["fresh_confirmation_opened"]
    assert not row["integrated_as_default_marking"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_margin_selection_prefers_the_existing_nonsaturated_model()
    print("tie-robust stage-local IQC marking audit passed")
