#!/usr/bin/env python3
"""Merge disjoint exact HNF-orbit shards with gap and overlap checks."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def actual_range(screen: dict) -> tuple[int, int]:
    start, configured_stop = screen["hnf_range"]
    visited = screen["hnf_visited"]
    stop = start + visited
    if stop > configured_stop:
        raise ValueError(f"visited orbit range exceeds configured range: {screen}")
    if screen.get("stopped_by") is None and stop != configured_stop:
        raise ValueError("terminal shard did not exhaust its configured orbit range")
    return start, stop


def merge_records(records: list[dict], copies: int) -> dict:
    if not records:
        raise ValueError("no orbit shards")
    records = sorted(records, key=lambda record: actual_range(record["periodic_z3"])[0])
    first = records[0]
    screens = [record["periodic_z3"] for record in records]
    if any(record["id"] != first["id"] for record in records):
        raise ValueError("candidate id mismatch")
    for field in ("hnf_total", "hnf_orbit_total"):
        if len({screen.get(field) for screen in screens}) != 1:
            raise ValueError(f"inconsistent {field}")
    if not all(screen.get("hnf_orbit_representatives") for screen in screens):
        raise ValueError("non-orbit shard supplied")
    if any(record["classification"] != "unresolved" for record in records):
        raise ValueError("positive or malformed shard supplied to negative merger")
    if any(screen.get("solver_unknown") != 0 for screen in screens):
        raise ValueError("cannot merge a shard with solver unknowns")

    cursor = 0
    receipts = []
    for screen in screens:
        start, stop = actual_range(screen)
        if start != cursor:
            raise ValueError(f"orbit range gap or overlap: expected {cursor}, found {start}")
        receipts.append({
            "orbit_range": [start, stop],
            "representatives": screen["hnf_visited"],
            "hnfs_covered": screen["hnf_covered"],
            "nodes": screen.get("exact_multicover_nodes", 0),
            "failed_states": screen.get("exact_multicover_failed_states", 0),
            "milliseconds": screen.get("milliseconds", 0),
        })
        cursor = stop

    orbit_total = screens[0]["hnf_orbit_total"]
    hnf_total = screens[0]["hnf_total"]
    complete = cursor == orbit_total
    covered = sum(receipt["hnfs_covered"] for receipt in receipts)
    if complete and covered != hnf_total:
        raise ValueError(f"complete orbit partition covers {covered}, expected {hnf_total}")
    merged = {
        "stopped_by": None if complete else "orbit_range_incomplete",
        "hnf_visited": sum(receipt["representatives"] for receipt in receipts),
        "hnf_covered": covered,
        "solver_unknown": 0,
        "exact_multicover_nodes": sum(screen.get("exact_multicover_nodes", 0) for screen in screens),
        "exact_multicover_failed_states": sum(screen.get("exact_multicover_failed_states", 0) for screen in screens),
        "exact_multicover_mitm_fallbacks": sum(screen.get("exact_multicover_mitm_fallbacks", 0) for screen in screens),
        "exact_multicover_mitm_pairs": sum(screen.get("exact_multicover_mitm_pairs", 0) for screen in screens),
        "exact_multicover_mitm_triples": sum(screen.get("exact_multicover_mitm_triples", 0) for screen in screens),
        "hnf_range": [0, cursor],
        "hnf_total": hnf_total,
        "hnf_orbit_representatives": True,
        "hnf_orbit_total": orbit_total,
        "hnf_range_exhausted": complete,
        "exhausted_by_copies": {str(copies): hnf_total} if complete else {},
        "milliseconds": sum(screen.get("milliseconds", 0) for screen in screens),
        "orbit_shard_receipts": receipts,
    }
    return {**first, "classification": "unresolved", "periodic_z3": merged}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--copies", type=int, required=True)
    args = parser.parse_args()
    grouped = defaultdict(list)
    for path in args.input:
        for line in Path(path).read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                grouped[record["id"]].append(record)
    merged = [merge_records(records, args.copies) for _, records in sorted(grouped.items())]
    Path(args.output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    print(json.dumps({
        "candidates": len(merged),
        "copies": args.copies,
        "complete": sum(record["periodic_z3"]["hnf_range_exhausted"] for record in merged),
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
