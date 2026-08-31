#!/usr/bin/env python3
"""Validate, merge, and compress two-copy substitution campaign receipts."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def read_ndjson(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validate(record: dict) -> tuple[str, int, bool]:
    detail = record["two_copy_alcove_metatile_screen"]
    key = record["id"], detail["scale"], bool(detail["include_reflections"])
    if detail.get("parents_completed") != detail.get("symmetry_distinct_metatiles"):
        raise RuntimeError(f"incomplete parent enumeration {key}")
    if record["classification"].startswith("no_two_copy_metatile_scalar"):
        if detail.get("certified") is not True or detail.get("closed_alphabet") is not None:
            raise RuntimeError(f"uncertified negative {key}")
    elif record["classification"] == "two_copy_metatile_substitution_system":
        if detail.get("certified") is not True or not detail.get("closed_alphabet"):
            raise RuntimeError(f"uncertified positive {key}")
    else:
        raise RuntimeError(f"inconclusive campaign row {key}")
    for parent in detail["parent_results"]:
        classification = parent["classification"]
        replay = (
            parent.get("local_obstruction_replay")
            if classification == "local_obstruction"
            else parent.get("exact_unsat_replay")
            if classification == "exact_unsat"
            else parent.get("replay")
            if classification == "mixed_metatile_rule"
            else None
        )
        if replay is None or replay.get("verified") is not True:
            raise RuntimeError(f"unreplayed parent {key} index={parent['parent_index']}")
    return key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-results", type=int, default=0)
    args = parser.parse_args()
    records = [record for path in args.inputs for record in read_ndjson(Path(path))]
    if args.expected_results and len(records) != args.expected_results:
        raise RuntimeError(f"expected {args.expected_results} rows, found {len(records)}")
    keys = [validate(record) for record in records]
    if len(set(keys)) != len(keys):
        raise RuntimeError("duplicate candidate/scale/model receipt")
    records.sort(key=lambda record: validate(record))
    output = Path(args.output)
    opener = gzip.open if output.suffix == ".gz" else open
    with opener(output, "wt", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(json.dumps({
        "results": len(records),
        "candidates": len({record["id"] for record in records}),
        "positive_systems": sum(
            record["classification"] == "two_copy_metatile_substitution_system"
            for record in records
        ),
        "output": str(output),
    }, indent=2))


if __name__ == "__main__":
    main()
