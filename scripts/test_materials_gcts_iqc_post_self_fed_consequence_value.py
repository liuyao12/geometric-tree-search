#!/usr/bin/env python3
"""Regression test for nested downstream IQC terminal value."""

import hashlib

from materials_gcts_iqc_post_self_fed_consequence_value import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, load_default_result)


def test_post_self_fed_consequence_value():
    row = load_default_result()
    if EXPECTED_FIXTURE_SHA256:
        assert hashlib.sha256(DEFAULT_FIXTURE.read_bytes()).hexdigest() == \
            EXPECTED_FIXTURE_SHA256
    assert row["children_advanced_target_free"]
    assert row["nested_supplied_groups"] == 9
    assert row["nested_selected_exact_groups"] == 3
    assert row["nested_selected_correct_sites"] == 18
    assert not row["development_gate_passed"]
    assert not row["target_used_for_consequence_fit_or_ranking"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_post_self_fed_consequence_value()
    print("post-self-fed consequence-value test passed")
