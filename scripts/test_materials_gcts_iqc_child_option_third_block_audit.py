#!/usr/bin/env python3

from materials_gcts_iqc_child_option_third_block_audit import (
    load_default_result)


def test_consumed_third_block_option_execution():
    row = load_default_result()
    assert len(row["receipt"]["groups"]) == 10
    assert all(len(group["parents"]) == 4
               for group in row["receipt"]["groups"])
    assert all(len(parent["selected_terminals"]) <= 4
               for group in row["receipt"]["groups"]
               for parent in group["parents"])
    assert row["selected_exact_parent_groups"] == 8
    assert row["complete_exact_third_block_supply_groups"] == 6
    assert row["exact_third_block_supply_groups"] == 3
    assert row["complete_exact_third_block_paths"] == 90
    assert row["exact_third_block_paths"] == 6
    assert sum(parent["terminal_candidates"]
               for group in row["receipt"]["groups"]
               for parent in group["parents"]) == 5091
    assert sum(len(parent["selected_terminals"])
               for group in row["receipt"]["groups"]
               for parent in group["parents"]) == 160
    assert row["receipt"]["target_open_count_before_receipt"] == 0
    assert row["target_open_count"] == 1
    assert not row["target_used_for_parent_or_terminal_candidates"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["marking_library_selects_one_winner"]
    assert not row["autonomous_commit_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_consumed_third_block_option_execution()
    print("IQC clusters-squared third-block supply: passed")
