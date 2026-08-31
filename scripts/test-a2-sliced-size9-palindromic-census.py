#!/usr/bin/env python3
"""Replay the complete size-nine palindromic-profile census screening chain."""

from __future__ import annotations

import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read_gzip_ndjson(name: str) -> list[dict]:
    with gzip.open(ROOT / "data" / name, "rt") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def assert_screen(rows: list[dict], copies: int, periodic: int, unresolved: int) -> None:
    assert len(rows) == periodic + unresolved
    assert sum(row["classification"] == "periodic" for row in rows) == periodic
    assert sum(row["classification"] == "unresolved" for row in rows) == unresolved
    for row in rows:
        screen = row["periodic_z3"]
        assert screen["solver_unknown"] == 0
        if row["classification"] == "periodic":
            assert screen["certificate"]["certified"] is True
            assert screen["certificate"]["copies"] == copies
            assert screen["replay"]["verified"] is True
        else:
            assert screen["hnf_range_exhausted"] is True
            assert str(copies) in screen["exhausted_by_copies"]


census = read_gzip_ndjson("a2-sliced-size9-palindromic-census.ndjson.gz")
exact_two = read_gzip_ndjson("a2-sliced-size9-palindromic-periodic-exact2.ndjson.gz")
exact_four = read_gzip_ndjson("a2-sliced-size9-palindromic-periodic-exact4.ndjson.gz")
four_representatives = read_gzip_ndjson(
    "a2-sliced-size9-palindromic-exact4-reflection-representatives.ndjson.gz"
)
exact_six = read_gzip_ndjson("a2-sliced-size9-palindromic-periodic-exact6.ndjson.gz")
six_representatives = read_gzip_ndjson(
    "a2-sliced-size9-palindromic-exact6-reflection-representatives.ndjson.gz"
)

assert len(census) == 1627
assert len({row["key"] for row in census}) == len(census)
assert all(row["id"].startswith("a2sp_9_") for row in census)
assert all(row["transverse_profile_class"] == "palindromic" for row in census)
assert all(row["morphology"]["transverse_profile_asymmetric"] is False for row in census)
assert all(row["source_complete_census_index"] == int(row["id"].split("_")[-1]) for row in census)

assert_screen(exact_two, copies=2, periodic=1135, unresolved=492)
assert {row["id"] for row in exact_two} == {row["id"] for row in census}

assert_screen(exact_four, copies=4, periodic=304, unresolved=188)
assert {row["id"] for row in exact_four} == {
    row["id"] for row in exact_two if row["classification"] == "unresolved"
}

assert len(four_representatives) == 114
assert {member for row in four_representatives for member in row["reflection_class"]["members"]} == {
    row["id"] for row in exact_four if row["classification"] == "unresolved"
}

assert_screen(exact_six, copies=6, periodic=17, unresolved=97)
assert {row["id"] for row in exact_six} == {row["id"] for row in four_representatives}
assert len(six_representatives) == 97
assert {row["id"] for row in six_representatives} == {
    row["id"] for row in exact_six if row["classification"] == "unresolved"
}
assert all(row["reflection_class"]["size"] == 1 for row in six_representatives)

print(
    "A2 size-nine palindromic-profile census chain replayed",
    {
        "complete_size9": 20980 + len(census),
        "two_copy_periodic": 1135,
        "four_copy_periodic": 304,
        "six_copy_periodic_classes": 17,
        "remaining_reflection_classes": len(six_representatives),
    },
)
