#!/usr/bin/env python3
"""Regression for the consumed local-section supply audit."""

from materials_gcts_iqc_local_section_consumed_supply_audit import (
    load_default_result)


def test_local_section_recovers_both_consumed_fresh_children() -> None:
    row = load_default_result()
    assert row["exact_child_groups"] == 4
    assert row["union_supplied_exact_child_groups"] == 4
    assert row["incremental_local_section_supply_groups"] == 2
    assert row["incremental_exact_nine_action_lineages"] == 20
    fresh = row["cases"][2]["exact_child_groups"]
    assert [(group["parent"], group["incremental_exact_children"])
            for group in fresh] == [(1, [8]), (7, [10])]
    assert all(group["third_block_incremental_audit"][0]
               ["exact_nine_action_lineages"] == 10 for group in fresh)
    assert not row["candidate_selection_target_used"]
    assert row["consumed_target_development_audit_only"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["winner_or_autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_local_section_recovers_both_consumed_fresh_children()
    print("consumed local-section IQC supply audit: passed")
