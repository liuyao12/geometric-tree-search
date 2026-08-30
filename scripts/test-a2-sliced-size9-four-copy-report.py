#!/usr/bin/env python3
"""Audit the archived reflected four-copy exclusion for size-nine A2 lead 11364."""

import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
archive = ROOT / "data/a2-sliced-alcove-size9-four-cluster-scale2-reflected-11364.ndjson.gz"
with gzip.open(archive, "rt") as stream:
    rows = [json.loads(line) for line in stream if line.strip()]
assert len(rows) == 1
record = rows[0]
detail = record["four_copy_alcove_metatile_screen"]
assert record["id"] == "a2sa_9_11364"
assert record["classification"] == "no_four_copy_metatile_scalar2_substitution"
assert detail["certified"] is True
assert detail["include_reflections"] is True
assert detail["symmetry_distinct_metatiles"] == 195075
assert detail["parent_range"] == [0, 195075]
assert detail["parents_completed"] == 195075
assert detail["parent_counts"] == {
    "atomic_local_obstruction": 195075,
    "local_obstruction": 0,
    "exact_unsat": 0,
    "mixed_metatile_rule": 0,
    "unresolved": 0,
}
cursor = 0
for receipt in detail["range_receipts"]:
    start, stop = receipt["parent_range"]
    assert start == cursor and start < stop <= 195075
    cursor = stop
assert cursor == 195075
assert len(detail["parent_results"]) == 195075
assert all(
    parent["parent_index"] == index
    and parent["classification"] == "atomic_local_obstruction"
    and parent["atomic_local_obstruction_replay"]["verified"] is True
    for index, parent in enumerate(detail["parent_results"])
)

print("A2 size-nine reflected four-copy archive regression passed")
