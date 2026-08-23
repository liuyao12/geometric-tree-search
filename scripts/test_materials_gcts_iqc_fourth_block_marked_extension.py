"""Contracts for available sealed marked fourth-block shards."""

from pathlib import Path

from materials_gcts_iqc_fourth_block_marked_extension import (
    ACTION_BUDGET, fixture_path, load_group)


def test_available_marked_shards_are_target_blind_and_reach_eight():
    assert ACTION_BUDGET == 8
    available = tuple(group for group in range(2, 5)
                      if Path(fixture_path(group)).exists())
    assert available, "at least one sealed marked shard is required"
    for group in available:
        row = load_group(group)
        assert row["group"] == group
        assert row["lineages_extended"] == 64
        assert row["lineages_replay_rejected"] + \
            row["lineages_continued"] == 64
        assert row["unique_geometry_expansions"] <= \
            row["naive_geometry_expansions"]
        assert row["saved_geometry_expansions"] == \
            row["naive_geometry_expansions"] - \
            row["unique_geometry_expansions"]
        assert row["development_targets_used_for_marking_fit"]
        assert not row["development_targets_reused"]
        assert not row["confirmation_target_opened"]
        assert not row["confirmation_target_used_for_marking_fit"]
        assert not row["target_used_for_extension"]
        assert not row["candidate_geometry_changed"]
        assert not row["winner_selected"]
        assert not row["autonomous_growth_claimed"]
        assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_available_marked_shards_are_target_blind_and_reach_eight()
    print("available marked fourth-block shards: passed")
