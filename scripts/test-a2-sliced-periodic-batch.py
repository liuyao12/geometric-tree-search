#!/usr/bin/env python3
"""Regression checks for resumable A2-sliced periodic orbit shards."""

import importlib.util
import gzip
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_periodic_batch",
    ROOT / "scripts" / "run-a2-sliced-periodic-batch.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_report(path, *, candidate_id="probe", classification="unresolved",
                 unknown=0, replay=False):
    path.write_text(json.dumps({
        "id": candidate_id,
        "classification": classification,
        "periodic_z3": {
            "hnf_range": [3, 4],
            "hnf_visited": 1,
            "stopped_by": None,
            "solver_unknown": unknown,
            "replay": {"verified": replay},
        },
    }) + "\n")


with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    shard = directory / "shard.ndjson"

    write_report(shard)
    assert MODULE.valid_shard(shard, "probe", 3, 4)

    # An unknown result is a valid, retained checkpoint, but it is not a
    # decided shard and therefore remains eligible for a later retry.
    write_report(shard, unknown=1)
    assert MODULE.valid_shard(shard, "probe", 3, 4, require_decided=False)
    assert not MODULE.valid_shard(shard, "probe", 3, 4, require_decided=True)

    write_report(shard, classification="periodic", replay=True)
    assert MODULE.valid_shard(shard, "probe", 3, 4)
    write_report(shard, classification="periodic", replay=False)
    assert not MODULE.valid_shard(shard, "probe", 3, 4)

    write_report(shard, candidate_id="other")
    assert not MODULE.valid_shard(shard, "probe", 3, 4)

    compressed = directory / "input.ndjson.gz"
    with gzip.open(compressed, "wt", encoding="utf-8") as stream:
        stream.write(json.dumps({"id": "compressed", "classification": "unresolved"}) + "\n")
    assert MODULE.read_ndjson(compressed) == [
        {"id": "compressed", "classification": "unresolved"}
    ]

print("A2-sliced resumable periodic batch regression passed")
