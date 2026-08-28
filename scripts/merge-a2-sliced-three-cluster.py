#!/usr/bin/env python3
"""Merge and validate disjoint three-copy alcove-metatile screen shards."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def read(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    expected = [record["id"] for record in read(Path(args.candidates))]
    by_id = {}
    for path in args.inputs:
        for record in read(Path(path)):
            if record["id"] in by_id:
                raise ValueError(f"duplicate candidate {record['id']}")
            by_id[record["id"]] = record
    if set(by_id) != set(expected):
        raise ValueError("three-copy metatile candidate coverage mismatch")
    merged = []
    counts = {}
    parent_counts = {}
    for candidate_id in expected:
        record = by_id[candidate_id]
        report = record["three_copy_alcove_metatile_screen"]
        kind = record["classification"]
        counts[kind] = counts.get(kind, 0) + 1
        if report["parents_completed"] != report["symmetry_distinct_metatiles"]:
            raise ValueError(f"incomplete parent alphabet for {candidate_id}")
        for parent in report["parent_results"]:
            parent_kind = parent["classification"]
            parent_counts[parent_kind] = parent_counts.get(parent_kind, 0) + 1
            replay_key = {
                "atomic_local_obstruction": "atomic_local_obstruction_replay",
                "local_obstruction": "local_obstruction_replay",
                "exact_unsat": "exact_unsat_replay",
                "mixed_metatile_rule": "replay",
            }.get(parent_kind)
            if replay_key is not None and not parent[replay_key]["verified"]:
                raise ValueError(f"unverified {parent_kind} for {candidate_id}")
            if replay_key is None and parent_kind != "unresolved":
                raise ValueError(f"unexpected parent result {parent_kind}")
        if kind.startswith("no_three_copy_metatile_") and not report["certified"]:
            raise ValueError(f"uncertified negative for {candidate_id}")
        if kind == "three_copy_metatile_substitution_system" and not report["closed_alphabet"]:
            raise ValueError(f"missing closed substitution alphabet for {candidate_id}")
        merged.append(record)
    serialized = "".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    )
    output = Path(args.output)
    if output.suffix == ".gz":
        with gzip.open(output, "wt", encoding="utf-8") as stream:
            stream.write(serialized)
    else:
        output.write_text(serialized)
    print(json.dumps({"records": len(merged), "counts": counts,
                      "parent_counts": parent_counts, "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
