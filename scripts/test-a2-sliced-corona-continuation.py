#!/usr/bin/env python3
"""Validate A2-sliced root-corona and radius-two GCTS receipts."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(name: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / "data" / name).read_text().splitlines()
            if line.strip()]


coronas = read("a2-sliced-alcove-size7-directed-corona1.ndjson")
assert len(coronas) == 259
assert all(record["corona_classification"] == "root_corona_exists" for record in coronas)
assert all(record["corona_z3"]["replay"]["verified"] for record in coronas)

# The exact corona-to-radius-two CEGAR must accept the alcove occupancy model,
# not just the legacy ``cells`` records.  Zero trials exercises construction
# without turning this regression into a solver benchmark.
cegar = load("a2_corona2_cegar_regression", "screen-a2-layered-corona2-cegar.py")
assert "cells" not in coronas[0]
construction = cegar.screen(coronas[0], trials=0, timeout_ms=1)
assert construction["corona2_classification"] == "unresolved"

extensions = read("a2-sliced-alcove-size7-retained-corona-extension.ndjson")
assert len(extensions) == 259
failed = [record for record in extensions if record[
    "retained_corona_extension_classification"] == "retained_corona_unextendible"]
unknown = [record for record in extensions if record[
    "retained_corona_extension_classification"] == "unresolved"]
assert len(failed) == 108
assert len(unknown) == 151
assert all(record["retained_corona_extension"]["outer_placement_indices"]
           for record in failed)
assert all(record["retained_corona_extension"]["claim_scope"]
           == "this_verified_first_corona_only" for record in failed)
assert all(record["retained_corona_extension"]["stopped_by"]
           == "solver_timeout" for record in unknown)

alternate = read("a2-sliced-alcove-size7-corona2-alternate.ndjson")
assert len(alternate) == 108
assert all(record["corona2_core_classification"] == "unresolved"
           for record in alternate)
assert sum(record["corona2_core_cegar"]["continuation_rounds"]
           for record in alternate) == 91

continued = read("a2-sliced-alcove-size7-corona2-continuation.ndjson")
assert len(continued) == 108
assert all(record["corona2_core_classification"] == "unresolved"
           for record in continued)
assert sum(len(record["corona2_core_cegar"]["clauses"])
           for record in continued) == 370
assert sum(record["corona2_core_cegar"]["rounds"]
           for record in continued) == 262
assert not any(record["corona2_core_cegar"]["outer_exhausted"]
               for record in continued)

print("A2-sliced corona continuation regression passed", {
    "root_coronas": len(coronas),
    "failed_retained_coronas": len(failed),
    "timeout_retained_coronas": len(unknown),
    "retained_clauses": 370,
    "cumulative_alternate_rounds": 262,
})
