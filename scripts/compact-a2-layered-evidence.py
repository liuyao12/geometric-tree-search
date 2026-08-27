#!/usr/bin/env python3
"""Compact exact A2 screening reports while retaining replayable summary evidence."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path


LARGE_RESULT_KEYS = {
    "parent_results",
    "results",
    "round_records",
}


def compact(value):
    if isinstance(value, list):
        return [compact(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: compact(item)
        for key, item in value.items()
        if key not in LARGE_RESULT_KEYS
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dedupe-by")
    args = parser.parse_args()

    records = []
    for pattern in args.input:
        matches = [Path(path) for path in sorted(glob.glob(pattern))]
        if not matches:
            raise SystemExit(f"input pattern matched no files: {pattern}")
        for path in matches:
            for line in path.read_text().splitlines():
                if line.strip():
                    records.append(compact(json.loads(line)))

    if args.dedupe_by:
        by_key = {}
        for record in records:
            by_key[record[args.dedupe_by]] = record
        records = list(by_key.values())

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n"
        for record in records
    ))
    print(json.dumps({"records": len(records), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
