#!/usr/bin/env python3
"""Structural regressions for the four-copy substitution census cache."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "a2_four_cluster", ROOT / "scripts" / "screen-a2-sliced-four-cluster-substitution.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.ENUMERATE_THREE is not module.enumerate_four_copy_metatiles

with tempfile.TemporaryDirectory() as directory:
    cache = Path(directory) / "enumeration.json"
    enumerated = {
        "raw_connected_extensions": 1,
        "symmetry_distinct_metatiles": 0,
        "canonical_sha256": "abc",
        "metatiles": [],
    }
    cache.write_text(json.dumps({
        "id": "probe",
        "include_reflections": True,
        "copies": 4,
        "enumerated": enumerated,
    }))
    assert module.cached_enumeration(
        {"id": "probe"}, True, cache
    ) == enumerated
    try:
        module.cached_enumeration({"id": "wrong"}, True, cache)
    except ValueError as error:
        assert "identity mismatch" in str(error)
    else:
        raise AssertionError("mismatched four-copy cache was accepted")

    sqlite_cache = Path(directory) / "enumeration.sqlite"
    connection = module.sqlite3.connect(sqlite_cache)
    connection.execute(
        "CREATE TABLE representatives (sort_key BLOB PRIMARY KEY, key_json TEXT, value_json TEXT) WITHOUT ROWID"
    )
    values = [
        {"alcoves": [{"base": [index, 0, 0], "order": [0, 1, 2]}],
         "canonical_key": [[index, 0, 0, "012"]]}
        for index in range(3)
    ]
    connection.executemany(
        "INSERT INTO representatives VALUES(?,?,?)",
        ((bytes([index]), json.dumps(value["canonical_key"]), json.dumps(value))
         for index, value in enumerate(values)),
    )
    connection.execute(
        "CREATE TABLE canonical_order (canonical_index INTEGER PRIMARY KEY, sort_key BLOB UNIQUE NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO canonical_order VALUES(?,?)",
        ((index, bytes([index])) for index in range(3)),
    )
    connection.execute(
        "CREATE TABLE metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL) WITHOUT ROWID"
    )
    metadata = {
        "id": "probe", "include_reflections": True, "copies": 4,
        "raw_connected_extensions": 4, "symmetry_distinct_metatiles": 3,
        "canonical_sha256": "digest", "three_copy_parent_total": 2,
        "three_copy_parent_range": [0, 2], "range_receipts": [],
    }
    connection.executemany(
        "INSERT INTO metadata VALUES(?,?)",
        ((key, json.dumps(value)) for key, value in metadata.items()),
    )
    connection.commit()
    connection.close()
    lazy = module.cached_enumeration({"id": "probe"}, True, sqlite_cache)
    assert len(lazy["metatiles"]) == 3
    assert lazy["metatiles"][0] == values[0]
    assert lazy["metatiles"][-1] == values[-1]

print("A2 four-copy substitution cache regression passed")
