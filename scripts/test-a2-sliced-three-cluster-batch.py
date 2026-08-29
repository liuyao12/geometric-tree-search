#!/usr/bin/env python3
"""Regression checks for resumable three-copy substitution parent ranges."""

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_three_batch", ROOT / "scripts" / "run-a2-sliced-three-cluster-batch.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
assert MODULE.terminate_active_processes() == 0


def report(start, stop, parents):
    return {
        "id": "probe",
        "classification": "unresolved",
        "three_copy_alcove_metatile_screen": {
            "certified": False,
            "scale": 3,
            "include_reflections": True,
            "family": "probe_family",
            "raw_connected_extensions": 2,
            "symmetry_distinct_metatiles": 2,
            "canonical_sha256": "abc",
            "oriented_metatile_types": 12,
            "parent_range": [start, stop],
            "parents_completed": stop - start,
            "closed_alphabet": None,
            "parent_counts": {},
            "parent_results": parents,
        },
    }


with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    left = directory / "left.ndjson"
    right = directory / "right.ndjson"
    left.write_text(json.dumps(report(0, 1, [{
        "parent_index": 0, "classification": "exact_unsat"
    }])) + "\n")
    right.write_text(json.dumps(report(1, 2, [{
        "parent_index": 1, "classification": "exact_unsat"
    }])) + "\n")
    assert MODULE.valid_shard(left, "probe", 0, 1)
    merged = MODULE.merge_candidate([right, left], 2)
    assert merged["classification"] == "no_three_copy_metatile_scalar3_substitution"
    detail = merged["three_copy_alcove_metatile_screen"]
    assert detail["certified"] is True
    assert detail["parent_counts"]["exact_unsat"] == 2

    positive = directory / "positive.ndjson"
    positive.write_text(json.dumps(report(0, 1, [{
        "parent_index": 0,
        "classification": "mixed_metatile_rule",
        "rule": [{"type_index": 0}],
    }])) + "\n")
    positive_merged = MODULE.merge_candidate([positive], 1)
    assert positive_merged["classification"] == "three_copy_metatile_substitution_system"
    assert positive_merged["three_copy_alcove_metatile_screen"]["closed_alphabet"] == [0]

    unknown = report(0, 1, [{"parent_index": 0, "classification": "unresolved"}])
    left.write_text(json.dumps(unknown) + "\n")
    assert MODULE.valid_shard(left, "probe", 0, 1, require_decided=False)
    assert not MODULE.valid_shard(left, "probe", 0, 1, require_decided=True)

print("A2 three-copy substitution batch regression passed")
