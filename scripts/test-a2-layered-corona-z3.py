#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")
DIRECT = load("a2_corona2_direct", "screen-a2-layered-corona2-direct.py")

root_records = [
    json.loads(line)
    for line in (ROOT / "data" / "a2-layered-size7-corona1-z3.ndjson").read_text().splitlines()
    if line.strip()
]
assert len(root_records) == 111
assert all(record["corona_classification"] == "root_corona_exists" for record in root_records)
assert all(record["corona_z3"]["replay"]["verified"] is True for record in root_records)

probe = root_records[0]
root = GEOMETRY.tile_occupancy(probe["cells"])
orientations = GEOMETRY.orientations(root)
placements = CORONA.candidate_placements(root, orientations)
placement_index = {
    (placement["orientation_index"], tuple(placement["translation"])): index
    for index, placement in enumerate(placements)
}
witness = [
    placement_index[(placement["orientation_index"], tuple(placement["translation"]))]
    for placement in probe["corona_z3"]["witness"]
]
assert CORONA.replay_corona(root, placements, witness)["verified"] is True

focused = [
    json.loads(line)
    for line in (ROOT / "data" / "a2-layered-size7-corona2-focused.ndjson").read_text().splitlines()
    if line.strip()
]
assert len(focused) == 8
assert all(record["corona2_classification"] == "unresolved" for record in focused)
assert all(record["corona2_cegar"]["outer_exhausted"] is False for record in focused)
assert all(record["corona2_cegar"]["first_coronas_rejected"] == 8 for record in focused)

deep = json.loads((ROOT / "data" / "a2-layered-size7-corona2-a2lp_7_00232-deep.ndjson").read_text())
assert deep["id"] == "a2lp_7_00232"
assert deep["corona2_classification"] == "unresolved"
assert deep["corona2_cegar"]["first_coronas_rejected"] == 64
assert deep["corona2_cegar"]["outer_exhausted"] is False

unit = DIRECT.screen({
    "id": "a2_unit_prism_control",
    "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
}, 10000, "default")
assert unit["corona2_direct_classification"] == "radius2_witness"
assert unit["corona2_direct"]["replay"]["verified"] is True

direct_timeout = json.loads(
    (ROOT / "data" / "a2-layered-size7-corona2-direct-a2lp_7_00232-qffd.ndjson").read_text()
)
assert direct_timeout["id"] == "a2lp_7_00232"
assert direct_timeout["corona2_direct_classification"] == "unresolved"
assert direct_timeout["corona2_direct"]["first_placements"] == 580
assert direct_timeout["corona2_direct"]["final_placements"] == 4643
assert direct_timeout["corona2_direct"]["final_incidences"] == 88217
assert direct_timeout["corona2_direct"]["stopped_by"] == "solver_timeout"

reduced_core = json.loads(
    (ROOT / "data" / "a2-layered-size7-corona2-core-a2lp_7_00232-minimized.ndjson").read_text()
)
assert reduced_core["id"] == "a2lp_7_00232"
assert reduced_core["classification"] == "sound_radius2_placement_obstruction"
assert len(reduced_core["source_outer_placement_indices"]) == 16
assert len(reduced_core["reduced_outer_placement_indices"]) == 12
assert reduced_core["minimal"] is False
assert reduced_core["initial_replay"]["result"] == "unsat"
assert reduced_core["final_replay"]["result"] == "unsat"

long_core = json.loads(
    (ROOT / "data" / "a2-layered-size7-corona2-core-a2lp_7_00232-long.ndjson").read_text()
)
assert long_core["id"] == "a2lp_7_00232"
assert long_core["corona2_core_classification"] == "unresolved"
assert long_core["corona2_core_cegar"]["outer_exhausted"] is False
assert long_core["corona2_core_cegar"]["rounds"] == 32
assert len(long_core["corona2_core_cegar"]["clauses"]) == 37
assert sum(
    clause.get("seeded") is True
    for clause in long_core["corona2_core_cegar"]["clauses"]
) == 5

print("A2 layered corona regression passed", {
    "root_coronas_replayed": len(root_records),
    "focused_candidates": len(focused),
    "distinct_first_coronas_rejected_each": 8,
    "deep_candidate_rejected_first_coronas": 64,
    "direct_positive_control": unit["corona2_direct"]["replay"]["patch_copies"],
    "sound_gcts_clauses": len(long_core["corona2_core_cegar"]["clauses"]),
})
