#!/usr/bin/env python3
"""Merge and validate disjoint retained-corona extension shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
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
        raise ValueError("retained-corona extension coverage mismatch")
    counts: dict[str, int] = {}
    merged = []
    for candidate_id in expected:
        record = by_id[candidate_id]
        kind = record["retained_corona_extension_classification"]
        report = record["retained_corona_extension"]
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "radius2_witness":
            if not report.get("replay", {}).get("verified"):
                raise ValueError(f"unverified radius-two witness for {candidate_id}")
        elif kind == "retained_corona_unextendible":
            indices = report.get("outer_placement_indices", [])
            if not indices or report.get("claim_scope") != "this_verified_first_corona_only":
                raise ValueError(f"invalid extension core for {candidate_id}")
        elif kind == "unresolved":
            if report.get("stopped_by") != "solver_timeout":
                raise ValueError(f"unexplained extension cutoff for {candidate_id}")
        else:
            raise ValueError(f"unexpected extension result {kind}")
        merged.append(record)
    Path(args.output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    print(json.dumps({"records": len(merged), "counts": counts,
                      "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
