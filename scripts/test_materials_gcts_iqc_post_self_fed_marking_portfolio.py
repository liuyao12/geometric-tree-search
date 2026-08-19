#!/usr/bin/env python3
"""Regression test for the bounded post-self-fed marking portfolio."""

import hashlib

from materials_gcts_iqc_post_self_fed_marking_portfolio import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, load_default_result)


def test_post_self_fed_marking_portfolio():
    row = load_default_result()
    if EXPECTED_FIXTURE_SHA256:
        assert hashlib.sha256(DEFAULT_FIXTURE.read_bytes()).hexdigest() == \
            EXPECTED_FIXTURE_SHA256
    assert row["supplied_groups"] == 9
    assert row["portfolio_exact_supplied_groups"] == 9
    assert row["portfolio_best_correct_sites"] == 28
    assert row["maximum_retained_candidates"] == 2
    assert row["total_retained_candidates"] == 19
    assert row["maximum_posthoc_attempt_to_exact"] == 2
    assert row["previous_rollback_width"] == 16
    assert row["bounded_rollback_supply_gate_passed"]
    assert not row["autonomous_commit_gate_passed"]
    assert not row["failure_detector_validated_target_free"]
    assert not row["target_used_for_fit_ranking_or_portfolio"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_post_self_fed_marking_portfolio()
    print("post-self-fed marking portfolio test passed")
