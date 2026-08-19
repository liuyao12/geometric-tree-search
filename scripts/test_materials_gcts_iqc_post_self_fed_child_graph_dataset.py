#!/usr/bin/env python3
"""Regression test for the frozen post-self-feed child graph corpus."""

import hashlib

from materials_gcts_iqc_post_self_fed_child_graph_dataset import (
    DEFAULT_FIXTURE, EXPECTED_FIXTURE_SHA256, load_graph_fixture,
    validate_dataset)


def test_child_graph_dataset():
    raw, row = load_graph_fixture(DEFAULT_FIXTURE)
    if EXPECTED_FIXTURE_SHA256:
        assert hashlib.sha256(raw).hexdigest() == EXPECTED_FIXTURE_SHA256
    validate_dataset(row)
    assert row["maximum_children"] == 8
    assert not row["target_used_for_graphs"]


if __name__ == "__main__":
    test_child_graph_dataset()
    print("post-self-fed child-graph dataset test passed")
