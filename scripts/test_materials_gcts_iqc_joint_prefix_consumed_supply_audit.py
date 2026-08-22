#!/usr/bin/env python3
"""Frozen regression for the consumed joint-prefix supply audit."""

from materials_gcts_iqc_joint_prefix_consumed_supply_audit import (
    load_default_result)


def test_consumed_supply():
    row = load_default_result()
    assert row["exact_child_groups"] == 6
    assert row["selected_exact_child_groups"] == 6
    assert row["exact_third_supplied_groups"] == 6
    assert row["all_consumed_groups_supply_exact_nine_action_lineage"]
    assert row["selected_prefixes_across_cases"] < \
        row["eager_prefixes_across_cases"]
    assert row["prefix_reduction_vs_eager"] > 0
    assert not row["candidate_selection_target_used"]
    assert row["consumed_target_development_audit_only"]


if __name__ == "__main__":
    test_consumed_supply()
    print("joint prefix consumed supply audit: passed")
