"""Contract for target-free fifth-block rollout receipts."""

from materials_gcts_iqc_fifth_block_rollout_preflight import (
    ROLLOUT_FEATURE_NAMES, load_default_result)


def test_fifth_block_rollout_is_bounded_and_target_blind():
    row = load_default_result()
    assert tuple(row["groups"]) == (2, 3, 4)
    assert row["shortlist_size_each"] == 32
    assert len(row["rollout_feature_names"]) == \
        len(ROLLOUT_FEATURE_NAMES) == 10
    assert all(len(group["rows"]) == 32 for group in row["group_rows"])
    assert row["candidate_receipts_frozen_before_rollout"]
    assert not row["targets_opened"]
    assert not row["target_or_correctness_used"]
    assert not row["candidate_geometry_changed"]
    assert not row["winner_selected"]


if __name__ == "__main__":
    test_fifth_block_rollout_is_bounded_and_target_blind()
    print("fifth-block rollout preflight: passed")
