#!/usr/bin/env python3
"""Merge disjoint exact HNF range reports into one certified exhaustion."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STAT_FIELDS = (
    "exact_multicover_nodes",
    "exact_multicover_failed_states",
    "exact_multicover_mitm_fallbacks",
    "exact_multicover_mitm_pairs",
    "exact_multicover_mitm_triples",
)


def load_one(path: Path) -> dict:
    records = [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    if len(records) != 1:
        raise ValueError(f"expected exactly one record in {path}")
    return records[0]


def merge(paths: list[Path]) -> dict:
    records = [(path, load_one(path)) for path in paths]
    candidate_ids = {record["id"] for _, record in records}
    if len(candidate_ids) != 1:
        raise ValueError(f"mixed candidates: {sorted(candidate_ids)}")
    positive = [record for _, record in records if record["classification"] == "periodic"]
    if positive:
        if not all(record["periodic_z3"]["replay"]["verified"] for record in positive):
            raise ValueError("unverified periodic certificate")
        return positive[0]

    totals = {record["periodic_z3"].get("hnf_total") for _, record in records}
    if len(totals) != 1 or None in totals:
        raise ValueError("inconsistent or missing HNF total")
    total = totals.pop()
    ordered = sorted(records, key=lambda item: item[1]["periodic_z3"]["hnf_range"])
    cursor = 0
    receipts = []
    aggregate = {field: 0 for field in STAT_FIELDS}
    milliseconds = 0
    for path, record in ordered:
        screen = record["periodic_z3"]
        start, stop = screen["hnf_range"]
        if start != cursor or not start < stop <= total:
            raise ValueError(f"HNF range gap or overlap at {path}: {[start, stop]}")
        if screen["hnf_visited"] != stop - start:
            raise ValueError(f"incomplete HNF range at {path}")
        if screen["solver_unknown"] != 0 or not screen["hnf_range_exhausted"]:
            raise ValueError(f"non-exhaustive HNF range at {path}")
        if record["classification"] != "unresolved" or screen.get("certificate"):
            raise ValueError(f"unexpected range classification at {path}")
        raw = path.read_bytes()
        receipts.append({
            "path": path.name,
            "hnf_range": [start, stop],
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
        for field in STAT_FIELDS:
            aggregate[field] += screen.get(field, 0)
        milliseconds += screen["milliseconds"]
        cursor = stop
    if cursor != total:
        raise ValueError(f"HNF ranges stop at {cursor}, expected {total}")

    base = ordered[0][1]
    receipt_stream = "\n".join(
        json.dumps(receipt, sort_keys=True, separators=(",", ":"))
        for receipt in receipts
    ).encode()
    return {
        **base,
        "classification": "unresolved",
        "periodic_z3": {
            "stopped_by": None,
            "engine": "exact_sparse_bitset_gcts_with_complete_2_plus_3_mitm_fallback",
            "hnf_visited": total,
            "solver_unknown": 0,
            **aggregate,
            "hnf_range": [0, total],
            "hnf_total": total,
            "hnf_range_exhausted": True,
            "exhausted_by_copies": {"6": total},
            "range_receipts": receipts,
            "receipt_stream_sha256": hashlib.sha256(receipt_stream).hexdigest(),
            "milliseconds": milliseconds,
            "milliseconds_semantics": "sum_of_disjoint_range_worker_times",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    paths = [Path(path) for path in args.inputs]
    report = merge(paths)
    Path(args.output).write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({
        "id": report["id"],
        "classification": report["classification"],
        "periodic_z3": report["periodic_z3"],
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
