"""Regression for the consumed-target fourth-block reach diagnosis."""

from materials_gcts_iqc_fourth_block_reach_diagnostic import \
    load_default_result


def test_exact_fourth_block_is_inside_frozen_geometry_but_outside_reach_eight():
    row = load_default_result()
    assert row["group"] == 0
    assert row["beam_exact_parent_count"] == 1
    assert row["replay_rejected_exact_parents"] == 0
    assert row["frontier_geometry_has_exact_path"]
    assert row["minimum_correct_rank_seen_by_depth"] == [7, 9, 9]
    assert row["minimum_uniform_reach_for_exact_path"] == 9
    assert row["minimum_rank_sum_for_exact_path"] == 25
    assert row["minimum_uniform_reach_for_exact_path"] > 8
    assert row["target_opened_only_for_diagnosis"]
    assert not row["target_used_for_deployable_ranking"]
    assert not row["diagnostic_path_returned_to_policy"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_exact_fourth_block_is_inside_frozen_geometry_but_outside_reach_eight()
    print("fourth-block reach diagnostic regression: passed")
