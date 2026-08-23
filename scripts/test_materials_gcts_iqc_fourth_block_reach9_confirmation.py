"""Regression for sealed reach-nine fourth-block proposal supply."""

from materials_gcts_iqc_fourth_block_reach9_confirmation import \
    load_default_result


def test_reach9_preserves_exact_parents_and_supplies_exact_fourth_blocks():
    row = load_default_result()
    assert row["source_action_budget"] == 9
    assert row["beam_exact_parents"] == 3
    assert row["exact_parents_continued"] == 3
    assert row["all_exact_parents_survived_replay"]
    assert row["successors"] == 12_861
    assert row["best_correct_actions"] == 12
    assert row["exact_twelve_action_successors"] == 61
    assert row["exact_successor_parent_count"] == 3
    assert row["frozen_geometry_reaches_exact_fourth_block"]
    assert row["target_opened_after_candidate_fixture"]
    assert not row["target_used_for_extension"]
    assert not row["target_used_for_ranking"]
    assert not row["exact_identities_returned_to_policy"]
    assert not row["autonomous_winner_selected"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_reach9_preserves_exact_parents_and_supplies_exact_fourth_blocks()
    print("reach-nine fourth-block confirmation: passed")
