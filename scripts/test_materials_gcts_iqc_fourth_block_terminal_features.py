"""Contract for target-blind fourth-block terminal feature receipts."""

from materials_gcts_iqc_fourth_block_terminal_features import (
    FEATURE_NAMES, GROUPS, load_default_result)


def test_terminal_features_are_frozen_before_any_group_target():
    row = load_default_result()
    assert tuple(row["groups"]) == GROUPS == (2, 3, 4)
    assert row["feature_count"] == len(FEATURE_NAMES) == 35
    assert tuple(group["candidates"] for group in row["group_rows"]) == \
        (8_382, 8_215, 8_649)
    assert row["total_candidates"] == 25_246
    assert not row["targets_opened"]
    assert not row["target_or_correctness_used"]
    assert not row["absolute_frame_or_raw_ids_in_features"]
    assert not row["candidate_geometry_changed"]
    assert all(not parent["target_used"]
               for group in row["group_rows"]
               for parent in group["parents"])


if __name__ == "__main__":
    test_terminal_features_are_frozen_before_any_group_target()
    print("fourth-block terminal feature receipt: passed")
