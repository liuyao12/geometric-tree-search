"""Regression for the width-eight parent-balanced fourth-block policy."""

from materials_gcts_iqc_fourth_block_parent_balanced_policy import (
    PARENT_WIDTH, load_default_result)


def test_width_eight_preserves_every_cross_nucleus_exact_parent():
    row = load_default_result()
    assert row["parent_width"] == PARENT_WIDTH == 8
    assert tuple(fold["exact_candidates_retained"]
                 for fold in row["outer_folds"]) == (36, 28)
    assert tuple(fold["exact_parents_retained"]
                 for fold in row["outer_folds"]) == (14, 16)
    assert tuple(fold["exact_parents"]
                 for fold in row["outer_folds"]) == (14, 16)
    assert all(fold["all_exact_parents_retained"]
               for fold in row["outer_folds"])
    assert row["selection_source_candidates"] == 8_649
    assert row["selected_candidates"] == 512
    assert not row["selection_target_opened"]
    assert not row["selection_target_used_for_fit_or_ranking"]
    assert not row["winner_selected"]
    assert not row["autonomous_growth_claimed"]


if __name__ == "__main__":
    test_width_eight_preserves_every_cross_nucleus_exact_parent()
    print("width-eight parent-balanced fourth-block policy: passed")
