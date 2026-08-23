"""Regression for the once-opened group-4 autonomous winner test."""

from materials_gcts_iqc_fourth_block_autonomous_confirmation import \
    load_default_result


def test_autonomous_confirmation_reports_exact_result_without_overclaim():
    row = load_default_result()
    assert row["group"] == 4
    assert row["candidates"] == 32
    assert row["exact_candidates"] == 0
    assert row["marked_first_exact_rank"] is None
    assert not row["marked_top_one_exact"]
    assert row["shuffle_top_one_exact_count"] == 0
    assert row["first_exact_rank_p_value"] == 1.
    assert not row["causal_autonomous_winner_gate_passed"]
    assert not row["autonomous_exact_fourth_block_continuation"]
    assert row["target_opened_once_after_all_orders_frozen"]
    assert not row["target_used_for_fit_ranking_or_execution"]
    assert row["candidate_receipt_unchanged_after_target"]
    assert not row["sustained_autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_autonomous_confirmation_reports_exact_result_without_overclaim()
    print("fourth-block autonomous confirmation: passed")
