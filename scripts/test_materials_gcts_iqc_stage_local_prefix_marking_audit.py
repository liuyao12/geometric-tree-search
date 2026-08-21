#!/usr/bin/env python3
"""Regression test for the stage-local IQC prefix marking gate."""

from materials_gcts_iqc_stage_local_prefix_marking_audit import (
    EXPECTED_AUDIT_DIGEST, evaluate)


def test_stage_local_prefix_marking_beats_matched_baseline_and_nulls():
    row = evaluate()
    selected = row["selected_result"]
    baseline = row["matched_current_pose_port_baseline"]
    assert row["audit_digest"] == EXPECTED_AUDIT_DIGEST
    assert row["rows_by_depth"] == (240, 776, 3300)
    assert row["exact_terminal_supply_groups"] == 20
    assert selected["budget"] == (2, 4, 1)
    assert tuple(stage["viable_groups"]
                 for stage in selected["stages"]) == (20, 20, 19)
    assert selected["exact_selected_groups"] == 19
    assert baseline["exact_selected_groups"] == 1
    assert row["shuffle_exact_group_maximum"] == 11
    assert row["shuffle_group_upper_tail_p"] == 1 / 32
    assert row["shuffle_row_upper_tail_p"] == 1 / 32
    assert row["stage_local_gate_passed"]
    assert row["within_group_species_stratified_site_shuffles"]
    assert row["prefix_consistency_preserved_in_nulls"]
    assert not row["targets_used_for_features_or_receipts"]
    assert not row["candidate_geometry_changed"]
    assert row["consumed_development_only"]
    assert not row["fresh_confirmation_opened"]
    assert not row["integrated_as_default_marking"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_stage_local_prefix_marking_beats_matched_baseline_and_nulls()
    print("stage-local IQC prefix marking audit regression passed")
