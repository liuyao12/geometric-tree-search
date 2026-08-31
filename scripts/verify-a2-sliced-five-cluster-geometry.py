#!/usr/bin/env python3
"""Independently replay every atomic obstruction in a five-copy cache."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_five_cluster",
    ROOT / "scripts" / "screen-a2-sliced-five-cluster-substitution.py",
)
FIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIVE)
TWO = FIVE.TWO
SUB = FIVE.SUB


def verify_range(task: dict) -> dict:
    record = next(item for item in TWO.read_ndjson(Path(task["input"]))
                  if item["id"] == task["id"])
    enumerated = FIVE.sqlite_enumeration(
        record, task["include_reflections"], Path(task["cache"])
    )
    metatiles = enumerated["metatiles"]
    alphabet = TWO.oriented_alphabet(
        [{"alcoves": record["alcoves"]}], task["include_reflections"]
    )
    digest = hashlib.sha256()
    for index in range(task["start"], task["stop"]):
        target = SUB.inflated_cells(metatiles[index]["alcoves"], task["scale"])
        uncovered = TWO.first_uncovered(target, alphabet)
        if uncovered is None:
            raise AssertionError(f"parent {index} has no atomic local obstruction")
        replay = TWO.replay_local_obstruction(target, alphabet, uncovered)
        if replay["verified"] is not True:
            raise AssertionError(f"parent {index} obstruction did not replay")
        digest.update(json.dumps(
            [index, list(uncovered), replay["placements_checked"]],
            separators=(",", ":"),
        ).encode())
        digest.update(b"\n")
    metatiles.connection.close()
    return {
        "parent_range": [task["start"], task["stop"]],
        "parents_replayed": task["stop"] - task["start"],
        "obstruction_receipts_sha256": digest.hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--parent-span", type=int, default=50000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output")
    args = parser.parse_args()

    record = next(item for item in TWO.read_ndjson(Path(args.input))
                  if item["id"] == args.candidate_id)
    enumerated = FIVE.sqlite_enumeration(
        record, args.include_reflections, Path(args.cache)
    )
    total = enumerated["symmetry_distinct_metatiles"]
    cache_identity = {
        "raw_connected_extensions": enumerated["raw_connected_extensions"],
        "symmetry_distinct_metatiles": total,
        "canonical_sha256": enumerated["canonical_sha256"],
        "four_copy_parent_total": enumerated["four_copy_parent_total"],
    }
    enumerated["metatiles"].connection.close()
    tasks = [{
        "input": str(Path(args.input).resolve()),
        "cache": str(Path(args.cache).resolve()),
        "id": args.candidate_id,
        "scale": args.scale,
        "include_reflections": args.include_reflections,
        "start": start,
        "stop": min(total, start + max(1, args.parent_span)),
    } for start in range(0, total, max(1, args.parent_span))]
    receipts = []
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=max(1, args.workers)) as pool:
        for receipt in pool.map(verify_range, tasks):
            receipts.append(receipt)
            print(json.dumps(receipt, separators=(",", ":")), flush=True)
    receipts.sort(key=lambda receipt: receipt["parent_range"][0])
    cursor = 0
    for receipt in receipts:
        if receipt["parent_range"][0] != cursor:
            raise AssertionError("geometric replay ranges are not contiguous")
        cursor = receipt["parent_range"][1]
    if cursor != total:
        raise AssertionError("geometric replay did not cover the complete alphabet")
    report = {
        "id": args.candidate_id,
        "verification": "independent_fresh_atomic_local_obstruction_replay",
        "scale": args.scale,
        "include_reflections": args.include_reflections,
        **cache_identity,
        "parents_replayed": sum(item["parents_replayed"] for item in receipts),
        "replay_failures": 0,
        "range_receipts": receipts,
    }
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
