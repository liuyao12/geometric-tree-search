#!/usr/bin/env python3
"""Regression checks for consecutive-layer alcove substitutions and reports."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "screen-a2-sliced-alcove-substitution.py"
SPEC = importlib.util.spec_from_file_location("a2_sliced_substitution", SCRIPT)
SUB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUB)


seed = [{"base": [0, 0, 0], "order": [0, 1, 2]}]
for scale in range(2, 6):
    assert len(SUB.inflated_cells(seed, scale)) == scale ** 3

control = {"id": "alcove_control", "alcoves": seed}
proper = SUB.screen(control, 2, 10_000, False)
assert proper["alcove_substitution_classification"] == "no_direct_scalar_substitution"
assert proper["alcove_substitution"]["independent_replay"]["verified"]
reflected = SUB.screen(control, 2, 10_000, True)
assert reflected["alcove_substitution_classification"] == "substitution_rule"
assert reflected["alcove_substitution"]["replay"]["verified"]
assert reflected["alcove_substitution"]["replay"]["patch_copies"] == 8

total = 0
atomic = 0
exact_cover = 0
for scale in range(2, 9):
    for model in ("proper", "reflected"):
        path = ROOT / "data" / f"a2-sliced-alcove-size7-substitution-scale{scale}-{model}.ndjson"
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert len(records) == 259
        assert all(record["alcove_substitution_classification"]
                   == "no_direct_scalar_substitution" for record in records)
        assert all(record["alcove_substitution"]["certified"] for record in records)
        assert all(record["alcove_substitution"]["scale"] == scale for record in records)
        assert all(record["alcove_substitution"]["include_reflections"]
                   == (model == "reflected") for record in records)
        for record in records:
            report = record["alcove_substitution"]
            if "atomic_uncovered_alcove" in report:
                assert report["independent_replay"]["verified"]
                atomic += 1
            else:
                assert report["nodes"] > 0
                assert report["failed_states"] > 0
                exact_cover += 1
        total += len(records)

assert total == 259 * 7 * 2
print("A2-sliced substitution regression passed", {
    "candidate_scale_models": total,
    "atomic_obstructions": atomic,
    "exact_cover_obstructions": exact_cover,
})
