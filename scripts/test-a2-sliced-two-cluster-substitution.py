#!/usr/bin/env python3
"""Regression checks for two-copy A2-sliced metatile substitutions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_two_cluster",
    ROOT / "scripts" / "screen-a2-sliced-two-cluster-substitution.py",
)
TWO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TWO)


control = {"id": "alcove_control", "alcoves": [
    {"base": [0, 0, 0], "order": [0, 1, 2]}
]}
proper = TWO.screen_candidate(control, 2, 10_000, False)
assert proper["classification"] == "no_two_copy_metatile_scalar2_substitution"
reflected = TWO.screen_candidate(control, 2, 10_000, True)
assert reflected["classification"] == "two_copy_metatile_substitution_system"
assert reflected["two_copy_alcove_metatile_screen"]["closed_alphabet"]
assert any(parent["classification"] == "mixed_metatile_rule"
           and parent["replay"]["verified"]
           for parent in reflected["two_copy_alcove_metatile_screen"]["parent_results"])

expected = {
    (2, "proper"): (5394, 3),
    (2, "reflected"): (11016, 25),
    (3, "proper"): (5394, 3),
    (3, "reflected"): (10927, 114),
}
total_parents = 0
for (scale, model), (local_count, exact_count) in expected.items():
    path = ROOT / "data" / f"a2-sliced-alcove-size7-two-cluster-scale{scale}-{model}.ndjson"
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len(records) == 259
    assert all(record["classification"]
               == f"no_two_copy_metatile_scalar{scale}_substitution"
               for record in records)
    parents = [parent for record in records
               for parent in record["two_copy_alcove_metatile_screen"]["parent_results"]]
    assert sum(parent["classification"] == "local_obstruction" for parent in parents) == local_count
    assert sum(parent["classification"] == "exact_unsat" for parent in parents) == exact_count
    assert all(parent["local_obstruction_replay"]["verified"]
               for parent in parents if parent["classification"] == "local_obstruction")
    assert all(parent["exact_unsat_replay"]["verified"]
               for parent in parents if parent["classification"] == "exact_unsat")
    total_parents += len(parents)

assert total_parents == 32876
print("A2-sliced two-copy substitution regression passed", {
    "candidate_scale_models": 259 * 4,
    "metatile_parents": total_parents,
    "control_closed_alphabet": reflected[
        "two_copy_alcove_metatile_screen"]["closed_alphabet"],
})
