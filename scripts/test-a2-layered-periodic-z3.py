#!/usr/bin/env python3
import importlib.util
import itertools
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_z3",
    ROOT / "scripts" / "screen-a2-layered-periodic-z3.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
MERGE_SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_exact_merge",
    ROOT / "scripts" / "merge-a2-layered-periodic-exact.py",
)
MERGE = importlib.util.module_from_spec(MERGE_SPEC)
MERGE_SPEC.loader.exec_module(MERGE)

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

# The complete bitset GCTS used for motifs of five copies and above agrees
# with an independent brute-force combination oracle on small multicovers.
for case in range(24):
    placements = [
        {"weights": [
            4 * ((case + 3 * index + 2 * residue) % 7)
            for residue in range(4)
        ]}
        for index in range(10)
    ]
    exact = MODULE.exact_weighted_multicover(placements, 4)
    brute = next((
        (0, *suffix)
        for suffix in itertools.combinations(range(1, len(placements)), 3)
        if all(
            sum(placements[index]["weights"][residue] for index in (0, *suffix)) == 48
            for residue in range(4)
        )
    ), None)
    assert (exact["result"] == "sat") == (brute is not None)
    if exact["chosen_indices"] is not None:
        assert len(set(exact["chosen_indices"])) == 4
        assert all(
            sum(
                placements[index]["weights"][residue]
                for index in exact["chosen_indices"]
            ) == 48
            for residue in range(4)
        )

# Force the seven-copy 3+3 fallback and compare its complete result with an
# independent brute-force oracle.  A one-node DFS budget makes every
# nontrivial instance enter the meet-in-the-middle path.
for case in range(24):
    placements = [
        {"weights": [
            4 * ((2 * case + 5 * index + 3 * residue) % 7)
            for residue in range(3)
        ]}
        for index in range(11)
    ]
    exact = MODULE.exact_weighted_multicover(placements, 7, dfs_node_limit=1)
    brute = next((
        (0, *suffix)
        for suffix in itertools.combinations(range(1, len(placements)), 6)
        if all(
            sum(placements[index]["weights"][residue] for index in (0, *suffix)) == 48
            for residue in range(3)
        )
    ), None)
    assert exact["used_mitm"] is True
    assert (exact["result"] == "sat") == (brute is not None)
    if exact["chosen_indices"] is not None:
        assert len(set(exact["chosen_indices"])) == 7
        assert all(
            sum(
                placements[index]["weights"][residue]
                for index in exact["chosen_indices"]
            ) == 48
            for residue in range(3)
        )

unit = {
    "id": "a2_periodic_exact_six_copy_control",
    "cells": [{"q": 0, "r": 0, "k": 0, "kind": "u"}],
}
unit_six = MODULE.screen_candidate(unit, SimpleNamespace(
    min_copies=6,
    max_copies=6,
    hnf_timeout_ms=1000,
    candidate_time_ms=0,
    solver="exact",
))
assert unit_six["classification"] == "periodic"
assert unit_six["periodic_z3"]["certificate"]["copies"] == 6
assert unit_six["periodic_z3"]["replay"]["verified"] is True
assert unit_six["periodic_z3"]["solver_unknown"] == 0
assert unit_six["periodic_z3"]["exact_multicover_nodes"] > 0

with tempfile.TemporaryDirectory() as temporary_directory:
    temporary = Path(temporary_directory)
    parts = []
    for part_index, bounds in enumerate(((0, 1), (1, 3))):
        part = temporary / f"part-{part_index}.ndjson"
        part.write_text(json.dumps({
            "id": "merge_control",
            "cells": unit["cells"],
            "classification": "unresolved",
            "periodic_z3": {
                "stopped_by": None,
                "hnf_visited": bounds[1] - bounds[0],
                "solver_unknown": 0,
                "exact_multicover_nodes": part_index + 2,
                "exact_multicover_failed_states": part_index + 1,
                "exact_multicover_mitm_fallbacks": part_index,
                "exact_multicover_mitm_pairs": 10 * part_index,
                "exact_multicover_mitm_triples": 20 * part_index,
                "hnf_range": list(bounds),
                "hnf_total": 3,
                "hnf_range_exhausted": True,
                "exhausted_by_copies": {},
                "milliseconds": 100 + part_index,
            },
        }, separators=(",", ":")) + "\n")
        parts.append(part)
    merged = MERGE.merge(parts)
    assert merged["periodic_z3"]["hnf_visited"] == 3
    assert merged["periodic_z3"]["exhausted_by_copies"] == {"6": 3}
    assert merged["periodic_z3"]["exact_multicover_nodes"] == 5
    assert len(merged["periodic_z3"]["range_receipts"]) == 2
    merged_seven = MERGE.merge(parts, copies=7)
    assert merged_seven["periodic_z3"]["exhausted_by_copies"] == {"7": 3}
    assert merged_seven["periodic_z3"]["mitm_partition"] == "3+3"

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

expected_exact_six = {
    "a2lp_7_00128": (20052090, 14804998),
    "a2lp_7_00211": (23166809, 15143212),
    "a2lp_7_00232": (17704350, 11832743),
    "a2lp_7_00235": (18596335, 12317275),
    "a2lp_7_00694": (6736205, 4959069),
    "a2lp_7_00755": (6479430, 4794297),
    "a2lp_7_00777": (6957313, 5177898),
    "a2lp_7_00809": (5756950, 4261827),
}
exact_six_records = []
for candidate_id, (nodes, failed_states) in expected_exact_six.items():
    record = json.loads((
        ROOT / "data" / f"a2-layered-size7-periodic-exact6-{candidate_id}.ndjson"
    ).read_text())
    screen = record["periodic_z3"]
    assert record["classification"] == "unresolved"
    assert screen["stopped_by"] is None
    assert screen["hnf_visited"] == 741
    assert screen["solver_unknown"] == 0
    assert screen["exhausted_by_copies"] == {"6": 741}
    assert screen["exact_multicover_nodes"] == nodes
    assert screen["exact_multicover_failed_states"] == failed_states
    exact_six_records.append(record)
assert sum(record["periodic_z3"]["hnf_visited"] for record in exact_six_records) == 5928
assert sum(
    record["periodic_z3"]["exact_multicover_nodes"] for record in exact_six_records
) == 105449482
assert sum(
    record["periodic_z3"]["exact_multicover_failed_states"]
    for record in exact_six_records
) == 73291319

exact_128_parts = [
    ROOT / "data" / f"a2-layered-size7-periodic-exact6-a2lp_7_00128-part{part}.ndjson"
    for part in range(1, 5)
]
merged_128 = MERGE.merge(exact_128_parts)
assert merged_128["periodic_z3"]["receipt_stream_sha256"] == (
    "375752a22a700c9aaf0172b24c4c9cd04075b9acaddacdded6695fe15212fd45"
)
assert merged_128["periodic_z3"]["exhausted_by_copies"] == {"6": 741}

print("A2 weighted periodic Z3 regression passed", {
    "former_survivor": candidate["id"],
    "copies": certificate["copies"],
    "determinant": certificate["determinant"],
    "size5_certificates": 45,
    "size6_certificates": 222,
    "size7_exact_through4_survivors": len(size_seven_survivors),
    "focused_exact_six_candidates": len(exact_six_records),
    "focused_exact_six_hnfs": 5928,
})
