#!/usr/bin/env python3
"""Regression loader for the consumed three-block rehearsal."""

from materials_gcts_iqc_three_block_portfolio_rehearsal import (
    load_default_result)


def test_consumed_rehearsal_is_honestly_scoped() -> None:
    row = load_default_result()
    assert row["end_to_end_candidate_supply"]
    assert row["lineage_candidates"] == 11808
    assert row["exact_lineages"] == 3
    assert row["exact_parent_ids"] == [8]
    assert row["exact_parent_child_ids"] == [[8, 123]]
    assert row["receipt"]["first_retained_stable_indices"] == [
        107, 0, 23, 4, 93, 34, 67, 40]
    assert row["receipt"]["selected_parent_ids"] == [7, 1, 8, 5]
    assert row["receipt_digest"] == \
        "2228dd53fc97e1a41b43a50b0a56adf6e4573c330204e20404e07ed1b484c65a"
    assert row["target_open_count"] == 1
    assert not row["target_used_for_candidate_or_ranking"]
    assert row["consumed_target_rehearsal_only"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_winner_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_consumed_rehearsal_is_honestly_scoped()
    print("consumed three-block portfolio rehearsal: passed")
