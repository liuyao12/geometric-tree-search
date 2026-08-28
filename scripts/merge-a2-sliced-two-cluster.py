#!/usr/bin/env python3
"""Merge and validate disjoint two-copy alcove-metatile screen shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    expected = [record["id"] for record in read(Path(args.candidates))]
    records = [record for path in args.inputs for record in read(Path(path))]
    by_id = {}
    for record in records:
        if record["id"] in by_id:
            raise ValueError(f"duplicate candidate {record['id']}")
        by_id[record["id"]] = record
    if set(by_id) != set(expected):
        raise ValueError("two-copy metatile candidate coverage mismatch")
    merged = []
    counts = {}
    parent_counts = {}
    for candidate_id in expected:
        record = by_id[candidate_id]
        kind = record["classification"]
        report = record["two_copy_alcove_metatile_screen"]
        counts[kind] = counts.get(kind, 0) + 1
        if report["parents_completed"] != report["symmetry_distinct_metatiles"]:
            raise ValueError(f"incomplete parent alphabet for {candidate_id}")
        for parent in report["parent_results"]:
            parent_kind = parent["classification"]
            parent_counts[parent_kind] = parent_counts.get(parent_kind, 0) + 1
            if parent_kind == "local_obstruction":
                if not parent["local_obstruction_replay"]["verified"]:
                    raise ValueError(f"unverified local obstruction for {candidate_id}")
            elif parent_kind == "exact_unsat":
                if not parent["exact_unsat_replay"]["verified"]:
                    raise ValueError(f"unverified exact UNSAT for {candidate_id}")
            elif parent_kind == "mixed_metatile_rule":
                if not parent["replay"]["verified"]:
                    raise ValueError(f"unverified metatile rule for {candidate_id}")
            elif parent_kind != "unresolved":
                raise ValueError(f"unexpected parent result {parent_kind}")
        if kind.startswith("no_two_copy_metatile_") and not report["certified"]:
            raise ValueError(f"uncertified negative for {candidate_id}")
        if kind == "two_copy_metatile_substitution_system" and not report["closed_alphabet"]:
            raise ValueError(f"missing closed substitution alphabet for {candidate_id}")
        merged.append(record)
    Path(args.output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    print(json.dumps({"records": len(merged), "counts": counts,
                      "parent_counts": parent_counts, "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
