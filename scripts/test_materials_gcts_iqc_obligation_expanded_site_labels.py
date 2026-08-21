"""Regression for the posthoc per-site obligation label companion."""

from collections import Counter

from materials_gcts_iqc_obligation_expanded_site_labels import (
    EXPECTED_DATASET_DIGEST, load_default_dataset)


def test_site_labels_reconcile_without_changing_frozen_geometry() -> None:
    row = load_default_dataset()
    labels = tuple(bool(value) for group in row["groups"]
                   for item in group["rows"]
                   for value in item["site_correct"])
    patterns = Counter(tuple(item["site_correct"])
                       for group in row["groups"]
                       for item in group["rows"])

    assert row["dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert len(row["groups"]) == 20
    assert len(labels) == 909
    assert sum(labels) == 462
    assert patterns[(True, True, True)] == 50
    assert patterns[(False, False, False)] == 46
    assert row["oracle_bound_plus_one_stable"]
    assert not row["source_geometry_changed"]
    assert row["labels_joined_posthoc_after_source_geometry_freeze"]
    assert row["consumed_development_only"]
    assert not row["fresh_confirmation_claimed"]


if __name__ == "__main__":
    test_site_labels_reconcile_without_changing_frozen_geometry()
    print("expanded obligation per-site labels: passed")
