#!/usr/bin/env python3

from materials_gcts_iqc_port_state_section_confirmation import evaluate


def test_port_state_section_confirmation_is_sealed_and_honest():
    report = evaluate()
    assert report.descriptor_version == "port-state-v2"
    assert not report.base_model_matches_published
    assert report.base_model_digest == (
        "d489513f7e5fa7966b0722e0a5f885e85bfdbe41bf13b51ff4f046747eeecbb5")
    assert report.self_fed_model_digest == (
        "0629b18ec9ec5a0dafaf6c1dcc34f31257adb0639ac9872a87c18c3489cdfe0b")
    assert report.teacher_forced_nuclei == 9
    assert report.teacher_first_exact_ranks == (1, 3, 8, 3, 7, 7, 7, 7, 4)
    assert report.self_fed_training_examples == 50065
    assert report.self_fed_training_colored_positives == 3677
    assert report.spatial_domains_disjoint
    assert report.target_materialized_after_execution
    assert not report.target_used_for_selection
    assert not report.stationary_or_exponential_certificate
    assert report.emitted_sites == report.correct_sites + report.false_sites
    assert report.candidate_bands_by_wave == (12, 12)
    assert report.selected_paths == ((1, 6, 8), (1, 7, 6))
    assert report.first_exact_ranks == (1, 1)
    assert report.emitted_sites_by_wave == (4, 4)
    assert report.correct_sites_by_wave == (4, 4)
    assert report.false_sites_by_wave == (0, 0)
    assert report.emitted_sites == report.correct_sites == 8
    assert report.precision == 1.
    assert report.two_wave_spatial_gate_passed


if __name__ == "__main__":
    test_port_state_section_confirmation_is_sealed_and_honest()
    print("IQC continuous port-state section tests: passed")
