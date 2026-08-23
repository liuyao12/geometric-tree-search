"""Contract for the target-sealed IQC autonomous winner preflight."""

from materials_gcts_iqc_fourth_block_autonomous_preflight import (
    SHUFFLES, load_default_result)


def test_autonomous_winner_and_null_orders_freeze_before_target():
    row = load_default_result()
    assert tuple(fold["first_exact_rank"] for fold in row["outer_folds"]) == \
        (5, 1)
    assert row["confirmation_candidates"] == len(row["marked_order"]) == 32
    assert row["shuffle_count"] == len(row["shuffle_orders"]) == SHUFFLES == 31
    assert not row["confirmation_target_opened"]
    assert not row["confirmation_target_used_for_fit_or_ranking"]
    assert row["winner_selected_before_target"]
    assert not row["winner_confirmed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_autonomous_winner_and_null_orders_freeze_before_target()
    print("fourth-block autonomous preflight: passed")
