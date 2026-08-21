#!/usr/bin/env python3
"""Regression for the incidence-ranked two-state rollback portfolio."""

from materials_gcts_iqc_incidence_ranked_rollback_portfolio import (
    load_default_result)


def test_incidence_ranked_rollback_portfolio():
    row = load_default_result()
    assert row["supplied_groups"] == 9
    assert row["retained_candidates"] == 19
    assert row["maximum_retained_candidates"] == 2
    assert row["selected_exact_supplied_groups"] == 9
    assert row["selected_correct_sites"] == 28
    assert row["development_gate_passed"] is True
    assert row["shuffle_exact_counts"].count(9) == 11
    assert row["shuffle_p"] == .375
    assert row["causal_shuffle_gate_passed"] is False
    assert row["outer_models_exclude_heldout_nucleus"] is True
    assert row["null_models_exclude_heldout_nucleus"] is True
    assert row["null_labels_shuffled_within_nucleus"] is True
    assert row["consumed_confirmation_candidate_count"] == 8
    assert row["consumed_confirmation_top_two_contains_exact"] is True
    assert row["consumed_confirmation_selected_exact"] is False
    assert row["failure_detector_validated_target_free"] is False
    assert row["target_used_for_fit_ranking_or_portfolio"] is False
    assert row["fresh_confirmation_claimed"] is False
    assert row["autonomous_commit_claimed"] is False


if __name__ == "__main__":
    test_incidence_ranked_rollback_portfolio()
    print("IQC incidence-ranked rollback portfolio tests passed")
