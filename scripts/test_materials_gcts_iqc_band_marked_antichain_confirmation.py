#!/usr/bin/env python3

import math

from materials_gcts_iqc_band_marked_antichain_confirmation import evaluate


def test_band_marked_antichain_confirmation_is_sealed_and_honest():
    report = evaluate()
    assert (report.seed_training_actions,
            report.seed_training_positive_actions) == (216, 57)
    assert (report.self_fed_training_actions,
            report.self_fed_training_positive_actions) == (216, 48)
    assert report.seed_band_model_digest == \
        "e414e95436b6872150d6a3f62b9bb0abb6c1f09f41b87f3d30e5436320c1b0bd"
    assert report.self_fed_band_model_digest == \
        "1d2611707869d63a748a9f29f9d425a8e8840563cf36dd9a88d0307c7a736aac"
    assert math.isinf(report.seed_threshold)
    assert math.isinf(report.self_fed_threshold)
    assert report.frozen_execution_digest == \
        "e1dc2b764185e3f62b479a6f279d288653de4a1b4938342528cefb5b585804ae"
    assert report.spatial_domains_disjoint
    calibrated = math.isfinite(report.seed_threshold) and \
        math.isfinite(report.self_fed_threshold)
    assert report.target_materialized_after_execution == calibrated
    assert not report.target_used_for_selection
    assert not report.stationary_or_exponential_certificate
    assert report.emitted_sites == report.correct_sites + report.false_sites
    assert report.executed_waves <= report.requested_waves
    assert report.executed_waves == 0
    assert not report.exact_three_wave_gate_passed
    assert not report.amplification_gate_passed
    assert all(row.accepted_bands <= row.eligible_bands
               for row in report.wave_audits)


if __name__ == "__main__":
    test_band_marked_antichain_confirmation_is_sealed_and_honest()
    print("IQC band-marked antichain confirmation tests: passed")
