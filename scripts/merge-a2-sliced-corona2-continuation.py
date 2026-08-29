#!/usr/bin/env python3
"""Replace bounded A2 sliced radius-two records with longer continuations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("continuations", nargs="+")
    args = parser.parse_args()

    baseline = read(Path(args.baseline))
    by_id = {record["id"]: record for record in baseline}
    if len(by_id) != len(baseline):
        raise ValueError("duplicate baseline candidate")

    replaced: set[str] = set()
    for path in args.continuations:
        for record in read(Path(path)):
            candidate_id = record["id"]
            if candidate_id not in by_id:
                raise ValueError(f"continuation outside baseline: {candidate_id}")
            if candidate_id in replaced:
                raise ValueError(f"duplicate continuation: {candidate_id}")
            if record["corona2_core_classification"] == "radius2_witness":
                if not record["corona2_core_cegar"].get("replay", {}).get("verified"):
                    raise ValueError(f"unverified witness: {candidate_id}")
            by_id[candidate_id] = record
            replaced.add(candidate_id)

    merged = [by_id[record["id"]] for record in baseline]
    counts: dict[str, int] = {}
    for record in merged:
        kind = record["corona2_core_classification"]
        counts[kind] = counts.get(kind, 0) + 1
    Path(args.output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    print(json.dumps({
        "records": len(merged),
        "continued": len(replaced),
        "counts": counts,
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
