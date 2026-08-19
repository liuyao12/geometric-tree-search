#!/usr/bin/env python3
"""Regression test for frozen post-self-feed consequence features."""

import hashlib

from materials_gcts_iqc_post_self_fed_consequence_dataset import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, FEATURE_NAMES,
    load_fixture_json, validate_dataset)


def test_frozen_consequence_dataset():
    raw, row = load_fixture_json()
    if EXPECTED_FIXTURE_SHA256:
        assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256
    validate_dataset(row)
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256
    assert row["maximum_children"] == 8
    assert len(FEATURE_NAMES) > 600
    assert not row["target_used_for_consequence_features"]
    assert row["labels_copied_from_consumed_development_fixture"]


if __name__ == "__main__":
    test_frozen_consequence_dataset()
    print("post-self-fed consequence dataset test passed")
