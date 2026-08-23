"""Regression for the consumed confirmation scorer failure."""

from materials_gcts_iqc_parent_balanced_confirmation_failure import (
    evaluate, validate_result)


def test_consumed_zero_is_not_reinterpreted_as_scientific_failure():
    row = validate_result(evaluate())
    assert row["candidate_actions"] == 512 * 12
    assert row["frozen_action_coordinate_decimals"] == 6
    assert row["failed_scorer_coordinate_decimals"] == 8
    assert row["authoritative_position_tolerance"] == 1e-5
    assert row["failure_class"] == "confirmation scorer precision mismatch"
    assert not row["reported_zero_exact_candidates_scientifically_interpretable"]
    assert not row["retry_same_nucleus_allowed"]


if __name__ == "__main__":
    test_consumed_zero_is_not_reinterpreted_as_scientific_failure()
    print("parent-balanced confirmation failure classification: passed")
