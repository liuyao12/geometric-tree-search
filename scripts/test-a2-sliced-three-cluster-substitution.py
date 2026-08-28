#!/usr/bin/env python3
"""Regression checks for three-copy A2-sliced metatile substitutions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_three_cluster",
    ROOT / "scripts" / "screen-a2-sliced-three-cluster-substitution.py",
)
THREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(THREE)


control = {"id": "alcove_control", "alcoves": [
    {"base": [0, 0, 0], "order": [0, 1, 2]}
]}
proper = THREE.screen_candidate(control, 2, 10_000, False)
assert proper["classification"] == "no_three_copy_metatile_scalar2_substitution"
reflected = THREE.screen_candidate(control, 2, 10_000, True)
assert reflected["classification"] == "three_copy_metatile_substitution_system"
assert reflected["three_copy_alcove_metatile_screen"]["closed_alphabet"]
assert all(parent["replay"]["verified"]
           for parent in reflected["three_copy_alcove_metatile_screen"]["parent_results"])

report_path = ROOT / "data" / "a2-sliced-alcove-size7-three-cluster-scale2-proper.ndjson"
if report_path.exists():
    records = [json.loads(line) for line in report_path.read_text().splitlines() if line.strip()]
    assert len(records) == 259
    assert all(record["classification"] == "no_three_copy_metatile_scalar2_substitution"
               for record in records)
    parents = [parent for record in records
               for parent in record["three_copy_alcove_metatile_screen"]["parent_results"]]
    assert sum(parent["classification"] == "atomic_local_obstruction"
               for parent in parents) == 128_339
    assert sum(parent["classification"] == "exact_unsat" for parent in parents) == 1
    assert all(parent["atomic_local_obstruction_replay"]["verified"]
               for parent in parents
               if parent["classification"] == "atomic_local_obstruction")
    assert all(parent["exact_unsat_replay"]["verified"]
               for parent in parents if parent["classification"] == "exact_unsat")
    print("A2-sliced three-copy substitution regression passed", {
        "candidates": len(records), "metatile_parents": len(parents),
        "control_closed_alphabet": reflected[
            "three_copy_alcove_metatile_screen"]["closed_alphabet"],
    })
else:
    print("A2-sliced three-copy control regression passed")
