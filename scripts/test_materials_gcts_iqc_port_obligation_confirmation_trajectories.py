#!/usr/bin/env python3
"""Regression for the target-free consumed-confirmation trajectories."""

from materials_gcts_iqc_port_obligation_confirmation_trajectories import (
    EXPECTED_CANDIDATE_DIGEST, EXPECTED_DATASET_DIGEST,
    EXPECTED_TARGET_FREE_RECEIPT_DIGEST, load_default_dataset)


def test_companion_reproduces_published_target_free_receipt() -> None:
    row = load_default_dataset()
    assert row["dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert row["source_target_free_receipt_digest"] == \
        EXPECTED_TARGET_FREE_RECEIPT_DIGEST
    assert row["source_candidate_digest"] == EXPECTED_CANDIDATE_DIGEST
    assert row["retained_candidates"] == 13
    assert row["candidate_counts_by_depth"] == [8, 40, 152]
    assert row["seed_atoms"] == 480
    assert not row["target_imported_or_constructed"]
    assert not row["target_labels_serialized"]
    assert not row["candidate_geometry_changed"]
    assert all(len(item["transitions"]) == 16
               for item in row["geometry_rows"])


if __name__ == "__main__":
    test_companion_reproduces_published_target_free_receipt()
    print("target-free obligation confirmation trajectories: passed")
