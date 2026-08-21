#!/usr/bin/env python3
"""External-transfer regression for the continuous common graph metric."""

from materials_gcts_iqc_external_port_incidence_metric_audit import evaluate


def test_external_port_metric_audit():
    report = evaluate()
    selected = report["development_selected"]
    assert selected["selected_exact_groups"] == 6
    assert selected["selected_groups"] == 6
    assert selected["selected_precision"] == 1.
    assert selected["spec"] == {
        "feature_variant": "pose+incidence", "neighbors": 13,
        "weighted": True, "admission_threshold": .7}
    assert report["wide_candidate_count"] == 28
    assert report["wide_candidate_groups"] == 3
    assert report["wide_supplied_groups"] == (0, 5)
    assert report["wide_selected_groups"] == 0
    assert report["wide_selected_exact_groups"] == 0
    assert report["wide_selected_false_groups"] == 0
    assert report["wide_exact_ranks"] == ((0, 5), (3, None), (5, 2))
    assert report["shuffle_trials"] == 31
    assert report["all_arms_use_identical_candidates"]
    assert report["wide_labels_joined_after_all_orders_freeze"]
    assert not report["wide_atoms_or_labels_used_for_fit_or_capacity"]
    assert not report["candidate_geometry_changed"]
    assert not report["integrated_as_default_marking"]
    assert not report["autonomous_growth_claimed"]
    assert not report["stationary_or_exponential_claimed"]
    assert not report["external_port_metric_gate_passed"]


if __name__ == "__main__":
    test_external_port_metric_audit()
    print("external port incidence metric audit passed")
