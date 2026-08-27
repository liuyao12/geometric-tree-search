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

print("A2 layered corona regression passed", {
    "root_coronas_replayed": len(root_records),
    "focused_candidates": len(focused),
    "distinct_first_coronas_rejected_each": 8,
    "deep_candidate_rejected_first_coronas": 64,
})
