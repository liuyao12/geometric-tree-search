#!/usr/bin/env python3

from materials_gcts_iqc_continuous_section_confirmation import evaluate


def test_continuous_section_confirmation_is_sealed_and_honest():
    report = evaluate()
    assert report.training_nuclei == 9
    assert report.training_examples == 49716
    assert report.training_colored_positives == 3695
    assert report.nuclei_with_exact_action_in_reach == 8
    assert report.continuous_model_digest == (
        "bb891f2c5055afe529c77c2834632c4df654bb2c9c944b1a4ae888535d980697")
    assert report.spatial_domains_disjoint
    assert report.target_materialized_after_trace_freeze
    assert not report.target_used_for_selection
    assert report.frozen_candidate_bands == 12
    assert report.confirmation_seed_atoms == 383
    assert report.confirmation_target_atoms == 1233
    assert report.selected_path_ranks == (1, 5, 12)
    assert report.first_exact_candidate_rank == 1
    assert report.emitted_sites == report.correct_sites == 4
    assert report.false_sites == 0
    assert report.precision == 1.
    assert report.continuous_spatial_gate_passed
    assert not report.stationary_or_exponential_certificate
    assert report.emitted_sites == report.correct_sites + report.false_sites


if __name__ == "__main__":
    test_continuous_section_confirmation_is_sealed_and_honest()
    print("IQC continuous-section confirmation tests: passed")
