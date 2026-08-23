"""Regression for the same-nucleus fourth-block marking ablation."""

from materials_gcts_iqc_fourth_block_marking_ablation import \
    load_default_result


def test_marked_and_unmarked_receipts_were_frozen_before_one_score():
    row = load_default_result()
    assert row["action_budget_each_arm"] == 8
    assert row["retained_parents_each_arm"] == 64
    assert row["both_candidate_receipts_frozen_before_target"]
    assert row["target_opened_once_after_both_receipts"]
    assert not row["target_used_for_either_extension"]
    assert row["candidate_geometry_generator_identical"]
    assert row["unmarked"]["successors"] == 8_028
    assert row["marked"]["successors"] == 8_215
    assert row["beam_exact_parents"] == 16
    assert row["unmarked"]["exact_twelve_action_successors"] == 96
    assert row["marked"]["exact_twelve_action_successors"] == 100
    assert row["unmarked"]["exact_successor_parent_count"] == 16
    assert row["marked"]["exact_successor_parent_count"] == 16
    assert row["marked_exact_supply_improved"]
    assert row["marked_parent_coverage_preserved"]
    assert row["marked_work_within_gate"]
    assert row["causal_marked_supply_gate_passed"]
    assert not row["autonomous_winner_selected"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_marked_and_unmarked_receipts_were_frozen_before_one_score()
    print("same-nucleus fourth-block marking ablation: passed")
