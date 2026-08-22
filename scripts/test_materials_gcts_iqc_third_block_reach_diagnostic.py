#!/usr/bin/env python3

from materials_gcts_iqc_third_block_reach_diagnostic import (
    load_default_result)


def test_consumed_missing_supply_reach_diagnostic():
    row = load_default_result()
    assert row["parents_diagnosed"] == 4
    assert len(row["parents"]) == 4
    assert row["current_reach"] == 8
    assert row["frontier_geometry_has_exact_path"] == 4
    assert row["current_reach_supplies_exact_path"] == 0
    assert row["maximum_required_uniform_reach"] == 12
    assert {parent["minimum_uniform_reach_for_exact_path"]
            for parent in row["parents"]} == {12}
    assert {parent["minimum_rank_sum_for_exact_path"]
            for parent in row["parents"]} == {21, 23}
    assert row["target_guided_diagnostic_only"]
    assert not row["target_used_for_deployable_candidate_selection"]
    assert not row["candidate_or_marking_changed"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_commit_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_consumed_missing_supply_reach_diagnostic()
    print("IQC missing third-block reach diagnosis: passed")
