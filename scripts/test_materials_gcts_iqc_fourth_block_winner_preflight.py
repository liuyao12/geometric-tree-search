"""Regression for the target-sealed fourth-block winner shortlist."""

from materials_gcts_iqc_fourth_block_winner_preflight import (
    SHORTLIST, load_default_result)


def test_winner_preflight_freezes_only_a_tree_search_shortlist():
    row = load_default_result()
    assert tuple(fold["first_exact_rank"] for fold in row["outer_folds"]) == \
        (17, 10)
    assert all(not fold["top_one_exact"] for fold in row["outer_folds"])
    assert row["confirmation_candidates"] == 8_649
    assert row["shortlist_size"] == len(row["shortlist"]) == SHORTLIST == 32
    assert not row["confirmation_target_opened"]
    assert not row["confirmation_target_used_for_fit_or_ranking"]
    assert not row["winner_selected"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_winner_preflight_freezes_only_a_tree_search_shortlist()
    print("fourth-block winner preflight: passed")
