#!/usr/bin/env python3
"""Merge disjoint A2-sliced radius-two core-CEGAR candidate shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-candidates", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    expected = {
        record["id"] for record in read(Path(args.seed_candidates))
        if record.get("retained_corona_extension_classification")
        == "retained_corona_unextendible"
    }
    records = [record for path in args.inputs for record in read(Path(path))]
    by_id = {}
    for record in records:
        if record["id"] in by_id:
            raise ValueError(f"duplicate candidate {record['id']}")
        by_id[record["id"]] = record
    if set(by_id) != expected:
        raise ValueError("radius-two CEGAR candidate coverage mismatch")
    counts: dict[str, int] = {}
    merged = []
    for candidate_id in sorted(expected):
        record = by_id[candidate_id]
        kind = record["corona2_core_classification"]
        report = record["corona2_core_cegar"]
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "radius2_witness":
            if not report.get("replay", {}).get("verified"):
                raise ValueError(f"unverified radius-two witness for {candidate_id}")
        elif kind == "radius2_obstruction_z3":
            if not report.get("outer_exhausted"):
                raise ValueError(f"uncertified radius-two obstruction for {candidate_id}")
        elif kind == "unresolved":
            if report.get("stopped_by") not in {"round_limit", "solver_timeout"}:
                raise ValueError(f"unexplained CEGAR cutoff for {candidate_id}")
        else:
            raise ValueError(f"unexpected CEGAR result {kind}")
        merged.append(record)
    Path(args.output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    print(json.dumps({"records": len(merged), "counts": counts,
                      "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
