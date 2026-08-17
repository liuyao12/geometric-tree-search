#!/usr/bin/env python3

from materials_gcts_iqc_spatial_width5_confirmation import evaluate


def test_width_five_fails_honestly_on_independent_spatial_nucleus():
    report = evaluate(1)
    result = report.result
    assert report.evaluation_domains_disjoint
    assert report.center_squared_norms_differ
    assert report.beam_width_frozen_before_confirmation
    assert result.spatial_domains_disjoint
    assert result.raw_execution_truth_fields_unavailable
    assert not result.target_used_for_selection
    assert result.initial_bounded_candidates == 5616
    assert result.initial_colored_correct_candidates == 431
    assert result.first_score_band_with_correct_site == 7
    assert result.first_pure_correct_score_band == 7
    assert result.selected_ranks == (5,)
    assert result.correct_sites == 0
    assert result.false_sites == 1
    assert not report.spatial_confirmation_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_width_five_fails_honestly_on_independent_spatial_nucleus()
    print("spatial width-five IQC confirmation tests: passed")
