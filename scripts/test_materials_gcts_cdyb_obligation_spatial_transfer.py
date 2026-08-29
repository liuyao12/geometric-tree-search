#!/usr/bin/env python3
"""Regression for consumed Cd--Yb whole-child spatial transfer."""

from materials_gcts_cdyb_obligation_spatial_transfer import evaluate


def test_cdyb_obligation_spatial_transfer():
    result = evaluate()
    assert result.training_windows == 5
    assert result.reserved_windows == 2
    assert result.training_atoms == 2385
    assert result.reserved_atoms == 959
    assert result.training_reserve_raw_id_intersection == 0
    assert result.spatial_domains_disjoint
    assert result.final_site_model_rows == 1245
    assert result.final_negative_actions > 0
    assert result.no_refit_on_reserved_windows
    assert result.reserved_windows_previously_consumed_by_reencoding
    assert not result.target_used_during_fit_enumeration_ranking_or_execution
    assert result.total_emitted_sites == (
        result.total_correct_sites + result.total_wrong_sites)
    assert result.total_emitted_sites == 81
    assert result.total_correct_sites == 81
    assert result.total_wrong_sites == 0
    assert result.completed_children == 11
    assert result.promoted_parents == 11
    assert result.self_fed_windows == 1
    assert result.aggregate_precision == 1
    assert result.aggregate_outer_recall == 0.09747292418772563
    assert result.windows[0].whole_candidates_by_wave == (0,)
    assert result.windows[1].accepted_sections_by_wave == (4, 4, 3)
    assert result.windows[1].correct_sites == 81
    assert result.spatial_transfer_gate_passed
    assert result.exact_execution_certificates
    assert all(len(item.first_wave_candidate_digest) == 64
               for item in result.windows)
    assert 0 <= result.aggregate_precision <= 1
    assert 0 <= result.aggregate_outer_recall <= 1
    assert "not fresh confirmation" in result.scientific_status
    assert len(result.audit_digest) == 64


if __name__ == "__main__":
    test_cdyb_obligation_spatial_transfer()
    print("CdYb whole-child spatial transfer: passed")
