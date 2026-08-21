#!/usr/bin/env python3
"""External-transfer regression for the shared port-incidence quotient."""

from materials_gcts_iqc_external_port_incidence_quotient_audit import evaluate


def test_external_port_incidence_audit():
    report = evaluate()
    assert report["wide_candidate_count"] == 28
    assert report["wide_candidate_groups"] == 3
    assert report["wide_supplied_groups"] == (0, 5)
    assert report["wide_known_candidates"] == 1
    assert report["wide_unknown_candidates"] == 27
    assert report["wide_recoverable_exact_groups"] == 0
    assert report["wide_selected_groups"] == 0
    assert report["wide_selected_exact_groups"] == 0
    assert report["wide_selected_false_groups"] == 0
    assert report["development_selected"]["selected_exact_groups"] == 4
    assert report["development_selected"]["selected_precision"] == 1.
    assert report["shuffle_trials"] == 31
    assert report["development_shuffle_exact_maximum"] >= 0
    assert report["exact_empirical_p"] == 1.
    assert report["false_empirical_p"] == 1.
    assert report["all_arms_use_identical_candidates"]
    assert report["wide_labels_joined_after_all_orders_freeze"]
    assert not report["wide_atoms_or_labels_used_for_fit_or_capacity"]
    assert report["unknown_semantic_types_fail_closed"]
    assert not report["candidate_geometry_changed"]
    assert not report["integrated_as_default_marking"]
    assert not report["autonomous_growth_claimed"]
    assert not report["stationary_or_exponential_claimed"]
    assert not report["external_port_incidence_gate_passed"]


if __name__ == "__main__":
    test_external_port_incidence_audit()
    print("external port incidence quotient audit passed")
