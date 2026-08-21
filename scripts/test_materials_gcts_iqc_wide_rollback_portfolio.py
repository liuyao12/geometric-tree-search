#!/usr/bin/env python3
"""Regression checks for the widened IQC rollback supply preflight."""

from materials_gcts_iqc_wide_rollback_portfolio import load_default_result


def test_wide_portfolio_restores_ambiguity_with_frozen_geometry():
    row = load_default_result()
    assert row["selected_candidates_per_marking"] == 8
    assert row["selected_total_retained_candidates"] == 120
    assert row["selected_maximum_retained_candidates"] == 16
    assert row["selected_exact_supplied_groups"] == 9
    assert row["selected_mixed_exact_inexact_groups"] == 7
    assert row["selected_best_correct_sites"] == 28
    assert row["selected_conditional_random_selector_exact_probability"] < .001
    assert row["restores_historical_width_without_exceeding_it"] is True
    assert row["wider_portfolio_preflight_passed"] is True
    assert row["typed_discharge_rollouts_constructed"] is False
    assert row["target_used_for_ranking_or_portfolio"] is False
    assert row["candidate_geometry_unchanged"] is True


if __name__ == "__main__":
    test_wide_portfolio_restores_ambiguity_with_frozen_geometry()
    print("wide rollback portfolio tests passed")
