#!/usr/bin/env python3
"""Merge disjoint candidate shards from the A2-sliced root-corona screen."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def read_ndjson(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()

    expected = [record["id"] for record in read_ndjson(Path(args.candidates))
                if record.get("classification") == "unresolved"]
    records = [record for path in args.inputs for record in read_ndjson(Path(path))]
    by_id: dict[str, dict] = {}
    for record in records:
        candidate_id = record["id"]
        previous = by_id.get(candidate_id)
        if previous is None:
            by_id[candidate_id] = record
            continue
        previous_kind = previous["corona_classification"]
        current_kind = record["corona_classification"]
        conclusive = {"root_corona_exists", "certified_no_root_corona"}
        if previous_kind in conclusive and current_kind in conclusive and previous_kind != current_kind:
            raise ValueError(f"conflicting corona results for {candidate_id}")
        if previous_kind == "unresolved" and current_kind in conclusive:
            by_id[candidate_id] = record
        elif previous_kind == current_kind == "unresolved":
            previous_nodes = previous["corona_z3"].get("exact_gcts", {}).get("nodes", 0)
            current_nodes = record["corona_z3"].get("exact_gcts", {}).get("nodes", 0)
            if current_nodes > previous_nodes:
                by_id[candidate_id] = record
    if set(by_id) != set(expected):
        raise ValueError("corona shard candidate coverage mismatch")

    counts: dict[str, int] = {}
    merged = []
    for candidate_id in expected:
        record = by_id[candidate_id]
        classification = record["corona_classification"]
        screen = record["corona_z3"]
        counts[classification] = counts.get(classification, 0) + 1
        if classification == "root_corona_exists":
            if not screen.get("replay", {}).get("verified"):
                raise ValueError(f"unverified corona witness for {candidate_id}")
        elif classification == "certified_no_root_corona":
            if not screen.get("certified") or screen.get("can_tile") is not False:
                raise ValueError(f"invalid corona obstruction for {candidate_id}")
        elif classification == "unresolved":
            if screen.get("stopped_by") not in {
                    "exact_gcts_node_limit", "solver_timeout"}:
                raise ValueError(f"unexplained corona cutoff for {candidate_id}")
        else:
            raise ValueError(f"unexpected corona classification {classification}")
        merged.append(record)

    Path(args.output).write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in merged)
    )
    print(json.dumps({"records": len(merged), "counts": counts,
                      "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
