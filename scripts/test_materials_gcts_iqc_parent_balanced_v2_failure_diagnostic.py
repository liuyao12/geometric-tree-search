"""Regression for the second fresh parent-selection failure boundary."""

from materials_gcts_iqc_parent_balanced_v2_failure_diagnostic import (
    evaluate, validate_result)


def test_valid_red_result_localizes_without_overclaim():
    row = validate_result(evaluate())
    assert row["raw_complete_nine_action_lineages"] == 1114
    assert row["retained_nine_action_parents"] == 64
    assert row["exact_first_nine_parent_count"] == 0
    assert row["exact_terminal_parent_count"] == 8
    assert row["failure_boundary"] == \
        "at or before the nine-action parent-balanced selection"
    assert not row["can_distinguish_raw_supply_failure_from_selector_loss"]
    assert row["fourth_block_exact_terminal_supply_present"]
    assert not row["target_reopened_or_execution_repeated"]


if __name__ == "__main__":
    test_valid_red_result_localizes_without_overclaim()
    print("second fresh parent-selection diagnostic: passed")
