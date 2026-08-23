"""Contract regression for completed target-blind fourth-block shards."""

from pathlib import Path

from materials_gcts_iqc_fourth_block_extension import (
    fixture_path, load_group)


def test_available_fourth_block_shards_are_target_blind():
    available = tuple(group for group in range(5)
                      if Path(fixture_path(group)).exists())
    assert available, "at least one durable extension shard is required"
    for group in available:
        row = load_group(group)
        assert row["group"] == group
        assert row["lineages_extended"] == 64
        assert row["lineages_replay_rejected"] + \
            row["lineages_continued"] == 64
        assert row["successors"] >= row["lineages_with_successors"]
        assert row["unique_geometry_expansions"] <= \
            row["naive_geometry_expansions"]
        assert row["saved_geometry_expansions"] == \
            row["naive_geometry_expansions"] - \
            row["unique_geometry_expansions"]
        assert not row["heldout_target_opened"]
        assert not row["target_used_for_extension"]
        assert not row["correctness_labels_present"]
        assert not row["winner_selected"]
        assert not row["autonomous_growth_claimed"]
        assert not row["stationary_or_exponential_claimed"]


if __name__ == "__main__":
    test_available_fourth_block_shards_are_target_blind()
    print("available fourth-block extension shards: passed")
