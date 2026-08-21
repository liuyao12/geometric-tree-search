#!/usr/bin/env python3
"""Regression for external recurrent macro-quotient transfer."""

from __future__ import annotations

from materials_gcts_iqc_external_recurrent_macro_quotient_audit import (
    evaluate)


def test_external_macro_transfer_is_sealed_and_honest():
    report = evaluate()
    assert report["wide_candidate_count"] == 28
    assert report["shuffle_trials"] == 31
    assert report["all_null_candidate_sets_identical"]
    assert report["wide_labels_joined_after_all_orders_freeze"]
    assert not report["wide_atoms_or_labels_used_for_fit_or_capacity"]
    assert not report["candidate_geometry_changed"]
    assert not report["raw_coordinates_ids_or_group_used_as_semantic_feature"]
    assert not report["autonomous_growth_claimed"]
    assert not report["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_external_macro_transfer_is_sealed_and_honest()
    print("external recurrent macro quotient audit passed")
