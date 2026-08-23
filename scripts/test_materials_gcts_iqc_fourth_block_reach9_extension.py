"""Contracts for the development-frozen reach-nine confirmation worker."""

from pathlib import Path

from materials_gcts_iqc_fourth_block_reach9_extension import (
    ACTION_BUDGET, DEVELOPMENT_GROUP, fixture_path, load_group)


def test_available_reach9_shards_remain_target_blind():
    assert ACTION_BUDGET == 9
    available = tuple(group for group in range(1, 5)
                      if Path(fixture_path(group)).exists())
    assert available, "at least one sealed reach-nine shard is required"
    for group in available:
        row = load_group(group)
        assert row["group"] == group
        assert row["development_group"] == DEVELOPMENT_GROUP
        assert row["lineages_extended"] == 64
        assert row["lineages_replay_rejected"] + \
            row["lineages_continued"] == 64
        assert row["unique_geometry_expansions"] <= \
            row["naive_geometry_expansions"]
        assert row["saved_geometry_expansions"] == \
            row["naive_geometry_expansions"] - \
            row["unique_geometry_expansions"]
        assert not row["development_target_reused"]
        assert not row["confirmation_target_opened"]
        assert not row["target_used_for_budget_selection"]
        assert not row["target_used_for_extension"]
        assert not row["winner_selected"]
        assert not row["autonomous_growth_claimed"]
        assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_available_reach9_shards_remain_target_blind()
    print("available reach-nine fourth-block shards: passed")
