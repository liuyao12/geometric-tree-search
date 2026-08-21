"""Regression for the sealed disjoint IQC obligation development corpus."""

from materials_gcts_iqc_obligation_expanded_dataset import (
    EXPECTED_DATASET_DIGEST, load_default_dataset)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    BATCH_SIZE, ROLLOUT_HORIZON)


def test_expanded_dataset_is_complete_stable_and_target_sealed() -> None:
    row = load_default_dataset()
    groups = tuple(row["groups"])
    rows = tuple(item for group in groups for item in group["rows"])

    assert row["dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert len(groups) == BATCH_SIZE == 20
    assert len(rows) == 303
    assert row["raw_rollout_domains_disjoint"]
    assert row["oracle_bound_plus_one_stable"]
    assert row["all_targets_constructed_after_all_geometry_froze"]
    assert not row["targets_used_for_fit_or_candidate_generation"]
    assert not row["candidate_geometry_changed"]
    assert not row["fresh_confirmation_claimed"]

    assert all(group["target_atoms"] > group["seed_atoms"] > 0
               for group in groups)
    assert all(0 < group["retained_candidates"] <= 16
               for group in groups)
    assert all(not group["target_received_by_worker"]
               and not group["target_used_for_candidate_or_rollout"]
               and group["labels_joined_after_all_geometry_froze"]
               for group in groups)
    assert all(len(item["transitions"]) == ROLLOUT_HORIZON
               and item["trace"]["accepted_children"] == ROLLOUT_HORIZON
               and not item["trace"]["target_used"] for item in rows)

    # Failure-rich and success-rich nuclei are both preserved.  This guards
    # against silently dropping the spatial domains that make transfer hard.
    exact_by_group = tuple(sum(bool(item["exact"])
                               for item in group["rows"])
                           for group in groups)
    assert exact_by_group == (
        0, 0, 0, 0, 10, 0, 6, 0, 1, 11,
        0, 0, 0, 5, 8, 8, 0, 0, 1, 0)


if __name__ == "__main__":
    test_expanded_dataset_is_complete_stable_and_target_sealed()
    print("expanded disjoint obligation dataset: passed")
