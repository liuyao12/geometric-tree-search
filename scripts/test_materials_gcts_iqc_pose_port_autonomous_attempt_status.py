#!/usr/bin/env python3

from materials_gcts_iqc_pose_port_autonomous_attempt_status import audit


def test_consumed_attempt_cannot_be_reused_or_claimed():
    report = audit()
    assert report.seed_materialized
    assert report.candidates_and_trace_computed
    assert report.target_factory_called
    assert not report.target_bound_plus_one_stable
    assert not report.target_score_computed
    assert not report.trace_digest_recovered
    assert not report.same_nucleus_retry_permitted
    assert "consumed/unknown" in report.outcome


if __name__ == "__main__":
    test_consumed_attempt_cannot_be_reused_or_claimed()
    print("autonomous attempt status test passed")
