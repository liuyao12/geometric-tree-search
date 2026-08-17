#!/usr/bin/env python3

from materials_gcts_iqc_continuous_section_multistep_confirmation import (
    evaluate)


def test_continuous_section_multistep_confirmation_is_sealed_and_honest():
    report = evaluate()
    assert report.model_matches_first_confirmation
    assert report.spatial_domains_disjoint
    assert report.requested_waves == 2
    assert report.executed_waves == 2
    assert report.continuous_model_digest == (
        "bb891f2c5055afe529c77c2834632c4df654bb2c9c944b1a4ae888535d980697")
    assert report.candidate_bands_by_wave == (12, 12)
    assert report.selected_paths == ((1, 5, 12), (1, 7, 8))
    assert report.first_exact_ranks == (1, 5)
    assert report.emitted_sites_by_wave == (4, 4)
    assert report.correct_sites_by_wave == (4, 0)
    assert report.false_sites_by_wave == (0, 4)
    assert report.correct_sites == report.false_sites == 4
    assert report.precision == .5
    assert report.target_materialized_after_execution
    assert not report.target_used_for_selection
    assert not report.stationary_or_exponential_certificate
    assert report.emitted_sites == report.correct_sites + report.false_sites
    assert not report.two_wave_spatial_gate_passed


if __name__ == "__main__":
    test_continuous_section_multistep_confirmation_is_sealed_and_honest()
    print("IQC continuous-section multistep confirmation tests: passed")
