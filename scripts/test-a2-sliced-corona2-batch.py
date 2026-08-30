#!/usr/bin/env python3
"""Regression checks for resumable A2-sliced radius-two batches."""

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_corona2_batch",
    ROOT / "scripts" / "run-a2-sliced-corona2-batch.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SCREEN_SOURCE = (ROOT / "scripts" / "screen-a2-layered-corona2-core-cegar.py").read_text()
assert SCREEN_SOURCE.index("for seed_core_path in args.seed_core:") < SCREEN_SOURCE.index(
    'output.write_text("")'
), "the exact screen must load an in-place continuation seed before truncating output"


def write_report(path, *, candidate_id="probe", classification="unresolved",
                 rounds=3, milliseconds=20, replay=False, outer_exhausted=False,
                 stopped_by="round_limit"):
    path.write_text(json.dumps({
        "id": candidate_id,
        "corona2_core_classification": classification,
        "corona2_core_cegar": {
            "outer_exhausted": outer_exhausted,
            "rounds": rounds,
            "cumulative_milliseconds": milliseconds,
            "clauses": [{"outer_placement_indices": [0]}] * rounds,
            "stopped_by": stopped_by,
            "replay": {"verified": replay},
        },
    }) + "\n")


with tempfile.TemporaryDirectory() as directory:
    directory = Path(directory)
    shard = directory / "probe.ndjson"
    checkpoint = directory / "checkpoint.ndjson"

    write_report(shard)
    assert MODULE.valid_shard(shard, "probe")
    assert not MODULE.valid_shard(shard, "probe", require_terminal=True)

    write_report(checkpoint, rounds=5, milliseconds=10)
    assert MODULE.best_seed_path(shard, checkpoint, "probe") == checkpoint
    write_report(checkpoint, rounds=6, milliseconds=10, stopped_by="in_progress")
    assert MODULE.best_seed_path(shard, checkpoint, "probe") == checkpoint
    write_report(shard, rounds=7, milliseconds=30)
    assert MODULE.best_seed_path(shard, checkpoint, "probe") == shard

    write_report(shard, classification="radius2_witness", replay=True,
                 stopped_by=None)
    assert MODULE.valid_shard(shard, "probe", require_terminal=True)
    write_report(shard, classification="radius2_witness", replay=False,
                 stopped_by=None)
    assert not MODULE.valid_shard(shard, "probe")

    write_report(shard, classification="radius2_obstruction_z3",
                 outer_exhausted=True, stopped_by=None)
    assert MODULE.valid_shard(shard, "probe", require_terminal=True)
    write_report(shard, candidate_id="other")
    assert not MODULE.valid_shard(shard, "probe")

print("A2-sliced radius-two batch regression passed")
