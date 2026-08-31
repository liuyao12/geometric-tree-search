#!/usr/bin/env python3
"""Replay the complete size-ten A2-sliced census and minimal quotient screen."""

from __future__ import annotations

import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read_gzip_ndjson(name: str) -> list[dict]:
    with gzip.open(ROOT / "data" / name, "rt") as stream:
        return [json.loads(line) for line in stream if line.strip()]


census = read_gzip_ndjson("a2-sliced-size10-complete-census.ndjson.gz")
exact_three = read_gzip_ndjson("a2-sliced-size10-periodic-exact3.ndjson.gz")
representatives = read_gzip_ndjson(
    "a2-sliced-size10-exact3-reflection-representatives.ndjson.gz"
)
focused_six = read_gzip_ndjson(
    "a2-sliced-size10-focused-periodic-exact6-bounded.ndjson.gz"
) + read_gzip_ndjson(
    "a2-sliced-size10-focused-periodic-exact6-ranks9-72.ndjson.gz"
)
focused_coronas = read_gzip_ndjson(
    "a2-sliced-size10-focused-corona1-bounded.ndjson.gz"
)

assert len(census) == 98537
assert len({row["id"] for row in census}) == len(census)
assert len({row["key"] for row in census}) == len(census)
assert all(row["id"] == f"a2sa_10_{index:05d}" for index, row in enumerate(census))
assert all(row["source_complete_census_index"] == index for index, row in enumerate(census))
assert {row["transverse_profile_class"] for row in census} == {
    "asymmetric", "palindromic"
}

assert len(exact_three) == len(census)
assert {row["id"] for row in exact_three} == {row["id"] for row in census}
assert sum(row["classification"] == "periodic" for row in exact_three) == 2558
assert sum(row["classification"] == "unresolved" for row in exact_three) == 95979
for row in exact_three:
    screen = row["periodic_z3"]
    assert screen["solver_unknown"] == 0
    if row["classification"] == "periodic":
        certificate = screen["certificate"]
        assert certificate["certified"] is True
        assert certificate["copies"] == 3
        assert certificate["determinant"] == 5
        assert screen["replay"]["verified"] is True
    else:
        assert screen["hnf_range_exhausted"] is True
        assert screen["hnf_covered"] == 31
        assert screen["hnf_orbit_total"] == 9
        assert screen["exhausted_by_copies"] == {"3": 31}

assert len(representatives) == 48209
assert all(row["survivor_count"] == len(representatives) for row in representatives)
assert {member for row in representatives for member in row["reflection_class"]["members"]} == {
    row["id"] for row in exact_three if row["classification"] == "unresolved"
}
assert all(row["reflection_class"]["size"] in (1, 2) for row in representatives)

assert len(focused_six) == 72
assert sum(row["classification"] == "periodic" for row in focused_six) == 59
assert sum(row["classification"] == "unresolved" for row in focused_six) == 13
for row in focused_six:
    screen = row["periodic_z3"]
    assert screen["solver_unknown"] == 0
    if row["classification"] == "periodic":
        assert screen["certificate"]["copies"] == 6
        assert screen["certificate"]["determinant"] == 10
        assert screen["replay"]["verified"] is True
    else:
        assert screen["hnf_range_exhausted"] is True
        assert screen["hnf_covered"] == 217
        assert screen["hnf_orbit_total"] == 47

assert len(focused_coronas) == 13
assert {row["id"] for row in focused_coronas} == {
    row["id"] for row in focused_six if row["classification"] == "unresolved"
}
assert all(row["corona_classification"] == "root_corona_exists"
           and row["corona_z3"]["replay"]["verified"] is True
           for row in focused_coronas)

print(
    "A2 size-ten complete census replayed",
    {
        "connected_tiles": len(census),
        "three_copy_periodic": 2558,
        "proper_survivors": 95979,
        "reflection_classes": len(representatives),
        "six_copy_periodic_in_ranked_72": 59,
        "six_copy_survivors_with_coronas": len(focused_coronas),
    },
)
