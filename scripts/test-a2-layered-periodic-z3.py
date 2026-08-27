#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_z3",
    ROOT / "scripts" / "screen-a2-layered-periodic-z3.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

size_five = [
    json.loads(line)
    for line in (ROOT / "data" / "a2-layered-size5-screen.ndjson").read_text().splitlines()
    if line.strip()
]
candidate = next(record for record in size_five if record["id"] == "a2lp_5_00003")
screened = MODULE.screen_candidate(candidate, SimpleNamespace(
    min_copies=1,
    max_copies=2,
    hnf_timeout_ms=5000,
    candidate_time_ms=0,
))
assert screened["classification"] == "periodic"
certificate = screened["periodic_z3"]["certificate"]
assert certificate["copies"] == 2
assert certificate["determinant"] == 5
assert screened["periodic_z3"]["replay"]["verified"] is True

occupancy = MODULE.tile_occupancy(candidate["cells"])
tile_orientations = MODULE.orientations(occupancy)
corrupt = {**certificate, "determinant": 6}
assert MODULE.replay_certificate(tile_orientations, corrupt) == {
    "verified": False,
    "reason": "determinant_mismatch",
}

for filename, expected_count, expected_copies in (
    ("a2-layered-size5-periodic-z3-all.ndjson", 45, 2),
    ("a2-layered-size6-periodic-z3-all.ndjson", 222, 1),
):
    records = [
        json.loads(line)
        for line in (ROOT / "data" / filename).read_text().splitlines()
        if line.strip()
    ]
    assert len(records) == expected_count
    assert all(record["classification"] == "periodic" for record in records)
    assert all(record["periodic_z3"]["replay"]["verified"] is True for record in records)
    assert all(record["periodic_z3"]["certificate"]["copies"] == expected_copies for record in records)

size_seven = [
    json.loads(line)
    for line in (ROOT / "data" / "a2-layered-size7-periodic-z3-through4.ndjson").read_text().splitlines()
    if line.strip()
]
assert len(size_seven) == 209
assert sum(record["classification"] == "periodic" for record in size_seven) == 98
size_seven_survivors = [record for record in size_seven if record["classification"] == "unresolved"]
assert len(size_seven_survivors) == 111
assert all(record["periodic_z3"]["exhausted_by_copies"] == {"4": 399} for record in size_seven_survivors)
assert all(record["periodic_z3"]["solver_unknown"] == 0 for record in size_seven_survivors)

print("A2 weighted periodic Z3 regression passed", {
    "former_survivor": candidate["id"],
    "copies": certificate["copies"],
    "determinant": certificate["determinant"],
    "size5_certificates": 45,
    "size6_certificates": 222,
    "size7_exact_through4_survivors": len(size_seven_survivors),
})
