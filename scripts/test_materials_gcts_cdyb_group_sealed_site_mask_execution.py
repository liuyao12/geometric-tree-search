#!/usr/bin/env python3
"""Regression for group-sealed Cd--Yb site-mask execution."""

from materials_gcts_cdyb_group_sealed_site_mask_execution import evaluate


def test_cdyb_group_sealed_site_mask_execution():
    result = evaluate()
    assert result.train_windows == 5
    assert result.vocabulary_atoms == 2385
    assert result.marking_fit_excludes_execution_window
    assert result.geometry_vocabulary_fit_on_all_training_windows
    assert not result.future_confirmatory_target_opened
    assert not result.target_api_present_during_execution
    assert len(result.held_windows) == result.train_windows
    assert all(item.fitted_marking_rows > 0 for item in result.held_windows)
    assert all(item.fitted_negative_rows > 0 for item in result.held_windows)
    assert all(len(item.first_wave_candidate_digest) == 64
               for item in result.held_windows)
    assert all(item.exact_certificates for item in result.held_windows)
    assert result.exact_execution_certificates
    assert result.total_emitted_sites == 9
    assert result.total_correct_sites == 8
    assert result.total_wrong_sites == 1
    assert result.aggregate_precision == 8 / 9
    assert result.nonempty_windows == 3
    assert result.self_fed_windows == 0
    assert result.completed_children == 0
    assert result.completed_parents == 0
    assert result.closure_total_emitted_sites == (
        result.closure_total_correct_sites + result.closure_total_wrong_sites)
    assert 0 <= result.closure_aggregate_precision <= 1
    assert result.closure_completed_children >= result.closure_promoted_parents
    assert result.closure_total_emitted_sites == 0
    assert result.closure_completed_children == 0
    assert result.closure_promoted_parents == 0
    assert result.closure_self_fed_windows == 0
    assert result.closure_candidate_batches_match_site_masks
    assert not result.obligation_closure_gate_passed
    assert all(item.closure_exact_certificates
               for item in result.held_windows)
    assert result.total_emitted_sites == (
        result.total_correct_sites + result.total_wrong_sites)
    assert 0 <= result.aggregate_precision <= 1
    assert 0 <= result.aggregate_outer_recall <= 1
    assert "development execution" in result.scientific_status
    assert len(result.audit_digest) == 64


if __name__ == "__main__":
    test_cdyb_group_sealed_site_mask_execution()
    print("CdYb group-sealed site-mask execution: passed")
