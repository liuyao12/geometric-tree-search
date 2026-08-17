#!/usr/bin/env python3

from materials_gcts_iqc_port_state_antichain_confirmation import evaluate


def test_port_state_antichain_confirmation_is_sealed_and_honest():
    report = evaluate()
    assert report.base_model_digest == \
        "d489513f7e5fa7966b0722e0a5f885e85bfdbe41bf13b51ff4f046747eeecbb5"
    assert report.self_fed_model_digest == \
        "0629b18ec9ec5a0dafaf6c1dcc34f31257adb0639ac9872a87c18c3489cdfe0b"
    assert (report.seed_threshold.candidate_rows,
            report.seed_threshold.accepted) == (49716, 50)
    assert (report.self_fed_threshold.candidate_rows,
            report.self_fed_threshold.accepted) == (50065, 24)
    assert report.executed_waves == 0
    assert report.frozen_execution_digest == \
        "59dae5dbd4714b264680c971b50b160e500d50e10e6042949a9be99b75a4021b"
    assert report.seed_threshold.false == 0
    assert report.self_fed_threshold.false == 0
    assert report.spatial_domains_disjoint
    assert report.target_materialized_after_execution
    assert not report.target_used_for_selection
    assert not report.stationary_or_exponential_certificate
    assert not report.exact_three_wave_gate_passed
    assert not report.amplification_gate_passed
    assert report.emitted_sites == report.correct_sites + report.false_sites


if __name__ == "__main__":
    test_port_state_antichain_confirmation_is_sealed_and_honest()
    print("IQC port-state antichain confirmation tests: passed")
