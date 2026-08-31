#!/usr/bin/env python3
"""Audit archived reflected four-copy exclusions for size-nine A2 leads."""

import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
for suffix, expected in (("11364", 195075), ("13833", 406896)):
    archive = ROOT / f"data/a2-sliced-alcove-size9-four-cluster-scale2-reflected-{suffix}.ndjson.gz"
    with gzip.open(archive, "rt") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    assert len(rows) == 1
    record = rows[0]
    detail = record["four_copy_alcove_metatile_screen"]
    assert record["id"] == f"a2sa_9_{suffix}"
    assert record["classification"] == "no_four_copy_metatile_scalar2_substitution"
    assert detail["certified"] is True
    assert detail["include_reflections"] is True
    assert detail["symmetry_distinct_metatiles"] == expected
    assert detail["parent_range"] == [0, expected]
    assert detail["parents_completed"] == expected
    assert detail["parent_counts"] == {
        "atomic_local_obstruction": expected,
        "local_obstruction": 0,
        "exact_unsat": 0,
        "mixed_metatile_rule": 0,
        "unresolved": 0,
    }
    cursor = 0
    for receipt in detail["range_receipts"]:
        start, stop = receipt["parent_range"]
        assert start == cursor and start < stop <= expected
        cursor = stop
    assert cursor == expected
    assert len(detail["parent_results"]) == expected
    assert all(
        parent["parent_index"] == index
        and parent["classification"] == "atomic_local_obstruction"
        and parent["atomic_local_obstruction_replay"]["verified"] is True
        for index, parent in enumerate(detail["parent_results"])
    )

print("A2 size-nine reflected four-copy archive regression passed")
