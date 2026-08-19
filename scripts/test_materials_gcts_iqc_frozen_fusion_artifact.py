#!/usr/bin/env python3
"""Fast integrity checks for the inert IQC fusion artifact."""

from __future__ import annotations

import bz2
import json

from materials_gcts_iqc_frozen_fusion_artifact import runtime_from_payload
from materials_gcts_iqc_frozen_fusion_runtime import (
    EXPECTED_ARTIFACT_DIGEST, EXPECTED_FUSION_MODEL_DIGEST,
    load_default_runtime)


def test_frozen_fusion_artifact_is_explicit_and_hash_checked():
    runtime = load_default_runtime()
    assert runtime["artifact_digest"] == EXPECTED_ARTIFACT_DIGEST
    assert runtime["fusion_model"].model_digest == \
        EXPECTED_FUSION_MODEL_DIGEST
    assert runtime["fusion_model"].scalar.representation.name == "incidence"
    assert runtime["fusion_model"].scalar.value.neighbors == 1
    assert runtime["fusion_model"].graph_rank_weight == 2.
    assert runtime["fusion_model"].graph.spec.objective == "pairwise"
    assert runtime["fusion_model"].graph.spec.interaction_order == 3
    assert len(runtime["grouped_vocabulary"].vocabulary.prototypes) == 53
    assert len(runtime["connection"].accepted_states) == 21841
    assert set(runtime["branch_models"]) == {
        "base", "colored", "ports", "coupled"}
    assert all(len(heads) == 3
               for heads in runtime["branch_models"].values())
    assert not runtime["grouped_vocabulary"].target_used
    assert runtime["provenance"]["new_development_atoms_seen"] is False
    assert runtime["provenance"]["new_development_targets_seen"] is False
    assert runtime["provenance"]["migration_python_version"].startswith(
        "3.9.6")


def test_artifact_mutation_fails_closed():
    from materials_gcts_iqc_frozen_fusion_runtime import DEFAULT_FIXTURE
    payload = json.loads(bz2.decompress(DEFAULT_FIXTURE.read_bytes()))
    payload["fusion_model"]["graph_rank_weight"] = 1.
    try:
        runtime_from_payload(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("mutated fusion artifact was accepted")


if __name__ == "__main__":
    test_frozen_fusion_artifact_is_explicit_and_hash_checked()
    test_artifact_mutation_fails_closed()
    print("frozen IQC fusion-artifact tests passed")
