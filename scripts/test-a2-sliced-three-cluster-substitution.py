#!/usr/bin/env python3
"""Regression checks for three-copy A2-sliced metatile substitutions."""

from __future__ import annotations

import importlib.util
import gzip
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
proper_control = THREE.screen_candidate(control, 2, 10_000, False)
assert proper_control["classification"] == "no_three_copy_metatile_scalar2_substitution"
reflected_control = THREE.screen_candidate(control, 2, 10_000, True)
assert reflected_control["classification"] == "three_copy_metatile_substitution_system"
closed = reflected_control["three_copy_alcove_metatile_screen"]["closed_alphabet"]
assert closed
assert all(parent["replay"]["verified"] for parent in
           reflected_control["three_copy_alcove_metatile_screen"]["parent_results"])

expected = {
    "proper": ("ndjson", {"atomic_local_obstruction": 128_339, "exact_unsat": 1}),
    "reflected": ("ndjson.gz", {"atomic_local_obstruction": 502_053, "exact_unsat": 276}),
}
total_parents = 0
for model, (extension, counts) in expected.items():
    report_path = (ROOT / "data" /
                   f"a2-sliced-alcove-size7-three-cluster-scale2-{model}.{extension}")
    if report_path.suffix == ".gz":
        with gzip.open(report_path, "rt", encoding="utf-8") as stream:
            records = [json.loads(line) for line in stream if line.strip()]
    else:
        records = [json.loads(line) for line in report_path.read_text().splitlines()
                   if line.strip()]
    assert len(records) == 259
    assert all(record["classification"] == "no_three_copy_metatile_scalar2_substitution"
               for record in records)
    assert all(record["three_copy_alcove_metatile_screen"]["certified"]
               for record in records)
    assert all(record["three_copy_alcove_metatile_screen"]["parents_completed"] ==
               record["three_copy_alcove_metatile_screen"]["symmetry_distinct_metatiles"]
               for record in records)
    parents = [parent for record in records
               for parent in record["three_copy_alcove_metatile_screen"]["parent_results"]]
    assert sum(parent["classification"] == "atomic_local_obstruction"
               for parent in parents) == counts["atomic_local_obstruction"]
    assert sum(parent["classification"] == "exact_unsat"
               for parent in parents) == counts["exact_unsat"]
    assert all(parent["atomic_local_obstruction_replay"]["verified"]
               for parent in parents
               if parent["classification"] == "atomic_local_obstruction")
    assert all(parent["exact_unsat_replay"]["verified"]
               for parent in parents if parent["classification"] == "exact_unsat")
    total_parents += len(parents)

assert total_parents == 630_669
print("A2-sliced three-copy substitution regression passed", {
    "candidate_models": 518,
    "metatile_parents": total_parents,
    "control_closed_alphabet": closed,
})
