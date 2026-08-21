#!/usr/bin/env python3
"""Regression checks for the wide typed-discharge IQC audit."""

from materials_gcts_iqc_typed_port_discharge_dataset import (
    load_default_dataset as load_narrow_dataset)
from materials_gcts_iqc_wide_typed_port_discharge_dataset import (
    load_default_dataset as load_wide_dataset)
from materials_gcts_iqc_wide_typed_port_discharge_rollback import (
    load_default_result as load_wide_scalar_result)
from materials_gcts_iqc_wide_typed_role_value import (
    load_default_result as load_role_result)


def test_wide_dataset_contains_the_identical_narrow_trajectories():
    narrow = load_narrow_dataset()
    wide = load_wide_dataset()
    assert wide["retained_candidates"] == 120
    assert wide["maximum_retained_candidates"] == 16
    assert wide["target_used_for_rollouts"] is False
    assert wide["candidate_geometry_unchanged"] is True
    wide_rows = {(group["group"], row["stable_index"]): row
                 for group in wide["groups"] for row in group["rows"]}
    for group in narrow["groups"]:
        for row in group["rows"]:
            other = wide_rows[group["group"], row["stable_index"]]
            assert other["trace"] == row["trace"]
            assert other["typed_transitions"] == row["typed_transitions"]
            assert other["exact"] == row["exact"]
            assert other["correct_sites"] == row["correct_sites"]


def test_wide_simple_typed_value_is_honestly_red():
    row = load_wide_scalar_result()
    assert row["mixed_exact_inexact_groups"] == 7
    assert row["typed_nested_exact_supplied_groups"] == 5
    assert row["typed_nested_correct_sites"] == 24
    assert row["scalar_nested_exact_supplied_groups"] == 7
    assert row["scalar_nested_correct_sites"] == 24
    assert row["typed_shuffle_upper_tail_p"] == .71875
    assert row["typed_lexicographically_beats_scalar"] is False
    assert row["failure_detector_validated_target_free"] is False


def test_identity_specific_role_value_is_honestly_red():
    row = load_role_result()
    assert row["spec_count"] == 120
    assert row["nested_selected_exact_supplied_groups"] == 5
    assert row["nested_selected_correct_sites"] == 23
    assert row["final_spec"] == {
        "aggregation": "mean", "horizon": 4, "minimum_groups": 2,
        "shrinkage": 1.0, "token_family": "coarse-role-status"}
    assert row["final_fitted_token_weights"] == 50
    assert row["shuffle_upper_tail_p"] == .71875
    assert row["development_gate_passed"] is False
    assert row["causal_superiority_gate_passed"] is False
    assert row["failure_detector_validated_target_free"] is False


if __name__ == "__main__":
    test_wide_dataset_contains_the_identical_narrow_trajectories()
    test_wide_simple_typed_value_is_honestly_red()
    test_identity_specific_role_value_is_honestly_red()
    print("wide typed port-discharge tests passed")
