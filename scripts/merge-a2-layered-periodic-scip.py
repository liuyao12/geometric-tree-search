#!/usr/bin/env python3
"""Merge disjoint proof-checked SCIP/VIPR orbit-range reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load_one(path: Path) -> dict:
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len(records) != 1:
        raise ValueError(f"expected exactly one record in {path}")
    return records[0]


def tool_fingerprint(screen: dict) -> dict:
    return {
        name: {key: value for key, value in identity.items() if key != "path"}
        for name, identity in screen["tools"].items()
    }


def merge(paths: list[Path]) -> dict:
    records = [(path, load_one(path)) for path in paths]
    ids = {record["id"] for _, record in records}
    if len(ids) != 1:
        raise ValueError(f"mixed candidates: {sorted(ids)}")

    positives = [record for _, record in records if record["classification"] == "periodic"]
    if positives:
        for record in positives:
            screen = record["periodic_exact_scip"]
            if not screen.get("certificate", {}).get("certified"):
                raise ValueError("periodic report lacks a certified quotient")
            if not screen.get("replay", {}).get("verified"):
                raise ValueError("periodic quotient lacks independent replay")
        certificates = {
            json.dumps(record["periodic_exact_scip"]["certificate"], sort_keys=True)
            for record in positives
        }
        if len(certificates) != 1:
            raise ValueError("conflicting periodic certificates")
        return positives[0]

    ordered = sorted(records, key=lambda item: item[1]["periodic_exact_scip"]["orbit_range"])
    screens = [record["periodic_exact_scip"] for _, record in ordered]
    scalar_fields = ("copies", "determinant", "hnf_total", "hnf_orbit_total")
    for field in scalar_fields:
        values = {screen.get(field) for screen in screens}
        if len(values) != 1 or None in values:
            raise ValueError(f"inconsistent {field}: {values}")
    fingerprints = {json.dumps(tool_fingerprint(screen), sort_keys=True) for screen in screens}
    if len(fingerprints) != 1:
        raise ValueError("worker tool binaries differ")

    cursor = screens[0]["orbit_range"][0]
    merged_start = cursor
    receipts = []
    range_receipts = []
    hnf_covered = 0
    milliseconds = 0
    for path, record in ordered:
        screen = record["periodic_exact_scip"]
        start, stop = screen["orbit_range"]
        if start != cursor or not start < stop <= screen["hnf_orbit_total"]:
            raise ValueError(f"orbit range gap or overlap at {path}: {[start, stop]}")
        if screen["orbit_representatives_visited"] != stop - start:
            raise ValueError(f"incomplete orbit range at {path}")
        proof_receipts = screen.get("proof_receipts", [])
        if len(proof_receipts) != stop - start:
            raise ValueError(f"missing proof receipts at {path}")
        if screen.get("solver_unknown") != 0:
            raise ValueError(f"solver unknown in {path}")
        if any(not receipt.get("verified") for receipt in proof_receipts):
            raise ValueError(f"unverified VIPR receipt in {path}")
        receipt_hnfs = sum(receipt["orbit_size"] for receipt in proof_receipts)
        if receipt_hnfs != screen["hnf_covered"]:
            raise ValueError(f"HNF coverage mismatch in {path}")
        raw = path.read_bytes()
        range_receipts.append({
            "path": path.name,
            "orbit_range": [start, stop],
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
        receipts.extend(proof_receipts)
        hnf_covered += screen["hnf_covered"]
        milliseconds += screen["milliseconds"]
        cursor = stop

    orbit_total = screens[0]["hnf_orbit_total"]
    complete = merged_start == 0 and cursor == orbit_total
    base = ordered[0][1]
    return {
        **base,
        "classification": "unresolved",
        "periodic_exact_scip": {
            "copies": screens[0]["copies"],
            "determinant": screens[0]["determinant"],
            "certified_no_periodic_quotient": complete,
            "orbit_range": [merged_start, cursor],
            "orbit_representatives_visited": cursor - merged_start,
            "hnf_covered": hnf_covered,
            "hnf_total": screens[0]["hnf_total"],
            "hnf_orbit_total": orbit_total,
            "solver_unknown": 0,
            "proof_receipts": receipts,
            "range_receipts": range_receipts,
            "milliseconds": milliseconds,
            "milliseconds_semantics": "sum_of_disjoint_range_worker_times",
            "tools": screens[0]["tools"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()
    report = merge([Path(value) for value in args.inputs])
    Path(args.output).write_text(json.dumps(report, separators=(",", ":")) + "\n")
    screen = report["periodic_exact_scip"]
    print(json.dumps({
        "id": report["id"],
        "classification": report["classification"],
        "orbit_range": screen.get("orbit_range"),
        "certified_no_periodic_quotient": screen.get("certified_no_periodic_quotient", False),
        "certificate": screen.get("certificate"),
    }, indent=2))


if __name__ == "__main__":
    main()
