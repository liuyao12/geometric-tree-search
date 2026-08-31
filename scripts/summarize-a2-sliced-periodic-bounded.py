#!/usr/bin/env python3
"""Validate and summarize a bounded orbit-sharded A2 periodic campaign."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate-ids", required=True)
    parser.add_argument("--copies", type=int, required=True)
    parser.add_argument("--orbit-total", type=int, required=True)
    parser.add_argument("--exact-node-limit", type=int, required=True)
    parser.add_argument(
        "--campaign",
        default="",
        help="stable campaign identifier; defaults to a copy-count-specific generic name",
    )
    args = parser.parse_args()
    directory = Path(args.input_dir)
    candidates = []
    positives = []
    campaign_digest = hashlib.sha256()
    for candidate_id in args.candidate_ids.split(","):
        candidate_id = candidate_id.strip()
        rows = []
        receipts = []
        positive_orbit = None
        for orbit in range(args.orbit_total):
            path = directory / f"{candidate_id}-orbits{orbit:03d}-{orbit + 1:03d}.ndjson"
            if not path.exists():
                if positive_orbit is not None:
                    break
                raise FileNotFoundError(path)
            payload = path.read_bytes()
            records = [json.loads(line) for line in payload.splitlines() if line.strip()]
            assert len(records) == 1 and records[0]["id"] == candidate_id
            record = records[0]
            detail = record["periodic_z3"]
            assert detail["hnf_range"] == [orbit, orbit + 1]
            assert detail["hnf_visited"] == 1
            assert detail["hnf_orbit_representatives"] is True
            assert detail["hnf_orbit_total"] == args.orbit_total
            assert record["classification"] in ("periodic", "unresolved")
            if record["classification"] == "periodic":
                assert detail["certificate"]["copies"] == args.copies
                assert detail["replay"]["verified"] is True
                positives.append({"id": candidate_id, "orbit": orbit})
                positive_orbit = orbit
            elif detail["solver_unknown"]:
                assert detail["solver_unknown"] == 1
                assert detail["exact_multicover_nodes"] > args.exact_node_limit
                assert detail["hnf_covered"] == 0
            else:
                assert detail["hnf_covered"] > 0
                assert detail["exact_multicover_nodes"] <= args.exact_node_limit
            digest = hashlib.sha256(payload).hexdigest()
            campaign_digest.update(f"{path.name}:{digest}\n".encode())
            receipts.append({
                "path": path.name,
                "sha256": digest,
                "orbit_range": [orbit, orbit + 1],
                "solver_unknown": detail["solver_unknown"],
                "exact_multicover_nodes": detail["exact_multicover_nodes"],
                "milliseconds": detail["milliseconds"],
            })
            rows.append(detail)
        unknown = sum(row["solver_unknown"] for row in rows)
        exact_negative = sum(
            row["solver_unknown"] == 0 and row.get("certificate") is None
            for row in rows
        )
        candidates.append({
            "id": candidate_id,
            "classification": "periodic" if positive_orbit is not None else "bounded_inconclusive",
            "periodic_orbit": positive_orbit,
            "orbit_total": args.orbit_total,
            "orbit_receipts": len(rows),
            "exact_negative_orbits": exact_negative,
            "node_capped_orbits": unknown,
            "hnf_total": rows[0]["hnf_total"],
            "hnfs_exactly_excluded": sum(row["hnf_covered"] for row in rows),
            "exact_multicover_nodes": sum(row["exact_multicover_nodes"] for row in rows),
            "exact_multicover_failed_states": sum(
                row["exact_multicover_failed_states"] for row in rows
            ),
            "milliseconds": sum(row["milliseconds"] for row in rows),
            "receipts": receipts,
        })
    result = {
        "campaign": args.campaign or (
            f"a2_sliced_periodic_copy{args.copies}_exact_gcts_bounded"
        ),
        "copies": args.copies,
        "exact_node_limit_per_orbit": args.exact_node_limit,
        "classification": "periodic" if positives else "bounded_inconclusive",
        "periodic_certificates": positives,
        "candidates": candidates,
        "campaign_receipt_sha256": campaign_digest.hexdigest(),
        "claim_scope": f"fixed_{args.copies}_copy_weighted_hnf_quotients",
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "classification": result["classification"],
        "candidates": [{
            "id": item["id"],
            "exact_negative_orbits": item["exact_negative_orbits"],
            "node_capped_orbits": item["node_capped_orbits"],
            "hnfs_exactly_excluded": item["hnfs_exactly_excluded"],
            "nodes": item["exact_multicover_nodes"],
            "seconds": round(item["milliseconds"] / 1000, 3),
        } for item in candidates],
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
