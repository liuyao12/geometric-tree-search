#!/usr/bin/env python3

from materials_gcts_iqc_self_fed_section_confirmation import evaluate


def test_self_fed_section_confirmation_is_sealed_and_honest():
    report = evaluate()
    assert report.base_model_matches_published
    assert report.teacher_forced_nuclei == 8
    assert report.teacher_first_exact_ranks == (1, 7, 3, 9, 9, 9, 9, 2)
    assert report.self_fed_training_examples == 44439
    assert report.self_fed_training_colored_positives == 3205
    assert report.self_fed_model_digest == (
        "0b5285e146ae6476cdbd2f098a99f2c4a473bc7c3f5a4b035cac93c01da16087")
    assert report.spatial_domains_disjoint
    assert report.target_materialized_after_execution
    assert not report.target_used_for_selection
    assert not report.stationary_or_exponential_certificate
    assert report.emitted_sites == report.correct_sites + report.false_sites
    assert report.candidate_bands_by_wave == (12, 12)
    assert report.selected_paths == ((1, 10, 6), (1, 11, 12))
    assert report.first_exact_ranks == (1, 4)
    assert report.correct_sites_by_wave == (4, 0)
    assert report.false_sites_by_wave == (0, 4)
    assert report.precision == .5
    assert not report.two_wave_spatial_gate_passed


if __name__ == "__main__":
    test_self_fed_section_confirmation_is_sealed_and_honest()
    print("IQC self-fed continuous-section tests: passed")
