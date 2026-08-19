#!/usr/bin/env python3
"""Regression for the target-free port-discharge rollback audit."""

from materials_gcts_iqc_post_self_fed_port_discharge_value import (
    load_default_result)


def test_port_discharge_value_audit():
    row = load_default_result()
    assert row["development_selected_exact_supplied_groups"] == 9
    assert row["development_selected_correct_sites"] >= 27
    assert row["nested_selected_exact_groups"] < 9
    assert row["fixed_point_traces"] == 0
    assert row["hard_exhaustion_certificate_available"] is False
    assert row["autonomous_commit_gate_passed"] is False
    assert row["failure_detector_validated_target_free"] is False
    assert row["target_used_for_rollout_fit_or_selection"] is False
    assert row["fresh_confirmation_claimed"] is False
    assert row["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_port_discharge_value_audit()
    print("post-self-fed port-discharge value tests passed")
