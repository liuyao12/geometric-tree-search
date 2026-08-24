#!/usr/bin/env python3
"""Serialization contract for the closure-conditioned child marking."""

from copy import deepcopy
import gzip
import json
import tempfile
from pathlib import Path

from materials_gcts_iqc_commuting_child_action_marking_fit import (
    EXPECTED_ARTIFACT_DIGEST,
    EXPECTED_MODEL_DIGEST,
    load_default_marking,
)


def test_default_child_marking_is_frozen_and_group_supplied() -> None:
    model, artifact = load_default_marking()
    selected = artifact["selected"]
    assert artifact["artifact_digest"] == EXPECTED_ARTIFACT_DIGEST
    assert artifact["model_digest"] == EXPECTED_MODEL_DIGEST
    assert model.model_digest == EXPECTED_MODEL_DIGEST
    assert artifact["training_rows"] == 3994
    assert artifact["positive_rows"] == 95
    assert selected["heldout_groups_supplied"] == 4
    assert selected["heldout_groups_with_positive_supply"] == 4
    assert selected["heldout_exact_parent_branches_supplied"] == 14
    assert selected["heldout_exact_parent_branches"] == 14
    assert selected["top_k"] == 16
    assert artifact["candidate_generation_target_used"] is False
    assert artifact["conditional_on_full_upstream_model"] is True
    assert artifact["fully_nested_upstream_selection"] is False


def test_artifact_mutation_fails_closed() -> None:
    _model, artifact = load_default_marking()
    altered = deepcopy(artifact)
    altered["selected"]["top_k"] = 1
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "altered.json.gz"
        path.write_bytes(gzip.compress(
            json.dumps(altered, sort_keys=True).encode(), mtime=0))
        try:
            load_default_marking(path)
        except AssertionError:
            pass
        else:
            raise AssertionError("mutated commuting child artifact accepted")


if __name__ == "__main__":
    test_default_child_marking_is_frozen_and_group_supplied()
    test_artifact_mutation_fails_closed()
    print("IQC commuting child marking artifact tests passed")
