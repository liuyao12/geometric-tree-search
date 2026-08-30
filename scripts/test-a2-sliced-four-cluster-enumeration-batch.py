#!/usr/bin/env python3
"""Regression checks for parallel four-copy canonical enumeration receipts."""

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_four_enumeration_batch",
    ROOT / "scripts" / "enumerate-a2-sliced-four-cluster-batch.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def metatile(value):
    return {
        "alcoves": [],
        "canonical_key": [[value, 0, 0, 0]],
        "base_decomposition": {},
    }


def receipt(start, stop, values):
    metatiles = [metatile(value) for value in values]
    return {
        "id": "probe",
        "include_reflections": True,
        "copies": 4,
        "enumerated": {
            "raw_connected_extensions": len(values) + 2,
            "symmetry_distinct_metatiles": len(metatiles),
            "canonical_sha256": MODULE.enumeration_digest(metatiles),
            "three_copy_parent_total": 4,
            "three_copy_parent_range": [start, stop],
            "metatiles": metatiles,
        },
    }


with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    left = directory / "left.json"
    right = directory / "right.json"
    left.write_text(json.dumps(receipt(0, 2, [0, 1])))
    right.write_text(json.dumps(receipt(2, 4, [1, 2])))
    assert MODULE.valid_shard(left, "probe", True, 0, 2, 4)
    assert not MODULE.valid_shard(left, "probe", False, 0, 2, 4)
    merged = MODULE.merge_shards([left, right], "probe", True, 4)
    assert merged["enumerated"]["symmetry_distinct_metatiles"] == 3
    assert merged["enumerated"]["raw_connected_extensions"] == 8
    assert merged["enumerated"]["three_copy_parent_range"] == [0, 4]
    assert len(merged["enumerated"]["range_receipts"]) == 2
    cache = directory / "merged.json"
    streamed = MODULE.merge_shards_to_cache([left, right], "probe", True, 4, cache)
    assert streamed["types"] == 3
    cached = json.loads(cache.read_text())
    assert cached["enumerated"]["canonical_sha256"] == merged["enumerated"]["canonical_sha256"]
    assert cached["enumerated"]["metatiles"] == merged["enumerated"]["metatiles"]
    assert MODULE.numeric_sort_key([[-2, 0, 1, "012"]]) < MODULE.numeric_sort_key([
        [10, 0, 1, "012"]
    ])

print("A2 four-copy enumeration batch regression passed")
