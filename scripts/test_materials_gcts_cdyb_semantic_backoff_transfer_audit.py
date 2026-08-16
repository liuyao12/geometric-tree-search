#!/usr/bin/env python3
"""Durable red gate for Cd--Yb semantic frozen-macro backoff."""

from materials_gcts_cdyb_semantic_backoff_transfer_audit import evaluate


def test_cdyb_missing_exact_macros_fail_closed_under_semantic_backoff():
    result = evaluate()
    assert result.train_windows == 5 and result.heldout_windows == 2
    assert result.train_atoms == 2385 and result.heldout_atoms == 959
    assert result.raw_id_intersection == 0
    assert result.frozen_l1_types == 80
    assert result.exact_transferred_types == 53
    assert result.missing_exact_types == 27
    assert result.missing_exact_type_ids == (
        5, 6, 7, 9, 10, 18, 20, 26, 27, 28, 29, 30, 31, 32, 33,
        44, 53, 54, 56, 58, 59, 61, 62, 63, 70, 74, 77)
    assert tuple(item.geometry_classes for item in result.descriptors) == (
        80, 80, 79, 77)
    assert all(item.recurrent_geometry_classes == 0
               for item in result.descriptors)
    assert all(item.safe_port_classes == 0 for item in result.descriptors)
    assert result.exact_derivation_backoff_types == 0
    assert result.best_safe_missing_coverage == 0
    assert result.exact_action_identity_preserved
    assert not result.heldout_used_to_fit_classes_or_thresholds
    assert not result.target_used_for_semantic_admission
    assert not result.family_cell_or_expected_scale_used
    assert not result.all_missing_exactly_recovered
    assert not result.gate_passed
    assert result.reason.startswith("red:")


if __name__ == "__main__":
    test_cdyb_missing_exact_macros_fail_closed_under_semantic_backoff()
    print("CdYb semantic backoff transfer audit: assertions passed")
