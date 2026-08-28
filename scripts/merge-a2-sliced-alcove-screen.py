#!/usr/bin/env python3
"""Merge disjoint candidate shards from the exact A2-sliced quotient screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_ndjson(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--copies", type=int, required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()

    census = read_ndjson(Path(args.census))
    expected_ids = [record["id"] for record in census]
    records = [record for path in args.inputs for record in read_ndjson(Path(path))]
    by_id: dict[str, dict] = {}
    for record in records:
        candidate_id = record["id"]
        if candidate_id in by_id:
            raise ValueError(f"duplicate candidate {candidate_id}")
        by_id[candidate_id] = record
    if set(by_id) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(by_id))
        extra = sorted(set(by_id) - set(expected_ids))
        raise ValueError(f"candidate coverage mismatch: missing={missing[:5]} extra={extra[:5]}")

    merged = [by_id[candidate_id] for candidate_id in expected_ids]
    periodic = 0
    survivors = 0
    for record in merged:
        screen = record.get("periodic_z3", {})
        if record["classification"] == "periodic":
            certificate = screen.get("certificate", {})
            replay = screen.get("replay", {})
            if (not certificate.get("certified")
                    or certificate.get("copies") != args.copies
                    or not replay.get("verified")):
                raise ValueError(f"invalid periodic certificate for {record['id']}")
            periodic += 1
            continue
        if record["classification"] != "unresolved":
            raise ValueError(f"unexpected classification for {record['id']}")
        if (screen.get("solver_unknown") != 0
                or not screen.get("hnf_range_exhausted")
                or str(args.copies) not in screen.get("exhausted_by_copies", {})):
            raise ValueError(f"incomplete negative screen for {record['id']}")
        survivors += 1

    Path(args.output).write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in merged)
    )
    print(json.dumps({
        "records": len(merged),
        "periodic": periodic,
        "survivors": survivors,
        "copies_exhausted": args.copies,
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
