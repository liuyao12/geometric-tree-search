#!/usr/bin/env python3
"""Regression contract for the consumed commuting-closure marking audit."""

from materials_gcts_iqc_commuting_closure_marking_benchmark import \
    load_default_result


def test_grouped_marking_supplies_every_development_nucleus() -> None:
    row = load_default_result()
    assert row["development_groups"] == 4
    assert row["development_examples"] == 224
    assert row["development_positive_examples"] == 16
    assert row["folds_with_exact_top8"] == 4
    assert row["development_gate_passed"] is True
    assert all(fold["top8_exact"] >= 1 for fold in row["folds"])
    assert all(fold["first_exact_rank"] <= 3 for fold in row["folds"])


def test_consumed_fresh_diagnostic_is_not_a_confirmation_claim() -> None:
    row = load_default_result()
    assert row["fresh_candidates"] == 56
    assert row["fresh_exact_candidates"] == 4
    assert row["fresh_top8_exact"] == 2
    assert row["fresh_first_exact_rank"] == 4
    assert row["selected_representation"] == "incidence"
    assert row["selected_neighbors"] == 1
    assert row["selected_graph_rank_weight"] == 0.0
    assert row["fresh_candidate_geometry_unchanged"] is True
    assert row["candidate_generation_target_used"] is False
    assert row["fresh_target_opened_only_after_candidate_freeze"] is True
    assert row["consumed_development_and_diagnostic_only"] is True
    assert row["future_confirmation_claimed"] is False
    assert row["autonomous_or_exponential_growth_claimed"] is False


if __name__ == "__main__":
    test_grouped_marking_supplies_every_development_nucleus()
    test_consumed_fresh_diagnostic_is_not_a_confirmation_claim()
    print("IQC commuting closure marking benchmark tests passed")
