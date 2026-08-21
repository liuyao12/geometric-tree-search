#!/usr/bin/env python3
"""Regression checks for the consumed stage-local IQC prefix corpus."""

from materials_gcts_iqc_stage_local_prefix_dataset import (
    EXPECTED_DATASET_DIGEST, EXPECTED_FIXTURE_SHA256, SCHEDULE,
    load_default_dataset)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    DEVELOPMENT_CENTERS)


def test_stage_local_prefix_dataset_is_sealed_and_complete():
    row = load_default_dataset()
    assert row["dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert len(EXPECTED_FIXTURE_SHA256) == 64
    assert tuple(row["schedule"]) == SCHEDULE
    assert len(row["groups"]) == len(DEVELOPMENT_CENTERS) == 20
    assert row["all_labels_joined_after_all_geometry_froze"]
    assert not row["targets_used_for_features_tree_or_branch_choice"]
    assert not row["candidate_geometry_changed"]
    assert not row["fresh_confirmation_claimed"]
    assert not row["autonomous_growth_claimed"]
    assert not row["stationary_or_exponential_claimed"]
    feature_widths = set()
    for group in row["groups"]:
        assert not group["target_received_by_worker"]
        assert not group["target_used_for_features_or_tree"]
        assert group["labels_joined_after_all_geometry_froze"]
        assert tuple(group["candidate_counts_by_depth"]) == tuple(
            len(stage["rows"]) for stage in group["stages"])
        assert tuple(stage["depth"] for stage in group["stages"]) == (1, 2, 3)
        for stage in group["stages"]:
            for candidate in stage["rows"]:
                feature_widths.add(len(candidate["features"]))
                assert candidate["correct_sites"] == sum(
                    candidate["site_correct"])
                assert candidate["viable_prefix"] == all(
                    candidate["site_correct"])
                assert len(candidate["action_key"]) == stage["depth"]
    assert feature_widths == {214}
    assert all(any(candidate["viable_prefix"]
                   for candidate in group["stages"][-1]["rows"])
               for group in row["groups"])


if __name__ == "__main__":
    test_stage_local_prefix_dataset_is_sealed_and_complete()
    print("stage-local IQC prefix dataset regression passed")
