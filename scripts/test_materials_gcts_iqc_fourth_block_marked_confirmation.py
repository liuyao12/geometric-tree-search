"""Regression for sealed marked reach-eight fourth-block supply."""

from materials_gcts_iqc_fourth_block_marked_confirmation import \
    load_default_result


def test_marked_reach8_transfers_exact_fourth_block_supply():
    row = load_default_result()
    assert row["source_action_budget"] == 8
    assert row["beam_exact_parents"] == 14
    assert row["exact_parents_continued"] == 14
    assert row["all_exact_parents_survived_replay"]
    assert row["successors"] == 8_382
    assert row["best_correct_actions"] == 12
    assert row["exact_twelve_action_successors"] == 82
    assert row["exact_successor_parent_count"] == 14
    assert row["marked_reach8_supplies_exact_fourth_block"]
    assert row["target_opened_after_candidate_fixture"]
    assert not row["target_used_for_extension"]
    assert not row["target_used_for_ranking"]
    assert not row["same_nucleus_unmarked_ablation_frozen_before_target"]
    assert not row["causal_marking_superiority_claimed"]
    assert not row["autonomous_winner_selected"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_marked_reach8_transfers_exact_fourth_block_supply()
    print("marked reach-eight fourth-block confirmation: passed")
