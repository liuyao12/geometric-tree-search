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

print("A2 four-copy substitution cache regression passed")
