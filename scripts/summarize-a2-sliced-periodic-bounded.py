#!/usr/bin/env python3
"""Validate and summarize a bounded orbit-sharded A2 periodic campaign."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument(
        "--retry-dir",
        action="append",
        default=[],
        help="optional selective-retry directory; may be repeated",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--receipt-archive",
        default="",
        help="optional gzip NDJSON archive of the strongest receipt per orbit",
    )
    parser.add_argument("--probe-dir", default="")
    parser.add_argument("--probe-solver", default="")
    parser.add_argument("--probe-timeout-ms", type=int, default=0)
    parser.add_argument("--candidate-ids", required=True)
    parser.add_argument("--copies", type=int, required=True)
    parser.add_argument("--orbit-total", type=int, required=True)
    parser.add_argument("--exact-node-limit", type=int, required=True)
    parser.add_argument(
        "--retry-node-limit",
        action="append",
        type=int,
        default=[],
        help="node limit corresponding to each retry stage, for reporting",
    )
    parser.add_argument(
        "--campaign",
        default="",
        help="stable campaign identifier; defaults to a copy-count-specific generic name",
    )
    args = parser.parse_args()
    directory = Path(args.input_dir)
    candidates = []
    positives = []
    selected_records = []
    campaign_digest = hashlib.sha256()
    for candidate_id in args.candidate_ids.split(","):
        candidate_id = candidate_id.strip()
        rows = []
        receipts = []
        positive_orbit = None
        for orbit in range(args.orbit_total):
            filename = f"{candidate_id}-orbits{orbit:03d}-{orbit + 1:03d}.ndjson"
            attempt_paths = [directory / filename]
            attempt_paths.extend(Path(item) / filename for item in args.retry_dir)
            if not attempt_paths[0].exists():
                if positive_orbit is not None:
                    break
                raise FileNotFoundError(attempt_paths[0])
            attempts = []
            for path in attempt_paths:
                if not path.exists():
                    continue
                payload = path.read_bytes()
                records = [json.loads(line) for line in payload.splitlines() if line.strip()]
                assert len(records) == 1 and records[0]["id"] == candidate_id
                attempt = records[0]
                detail = attempt["periodic_z3"]
                assert detail["hnf_range"] == [orbit, orbit + 1]
                assert detail["hnf_visited"] == 1
                assert detail["hnf_orbit_representatives"] is True
                assert detail["hnf_orbit_total"] == args.orbit_total
                digest = hashlib.sha256(payload).hexdigest()
                campaign_digest.update(f"{path.parent.name}/{path.name}:{digest}\n".encode())
                attempts.append((attempt, path, digest))
            periodic_attempts = [item for item in attempts if item[0]["classification"] == "periodic"]
            exact_attempts = [item for item in attempts
                              if item[0]["periodic_z3"]["solver_unknown"] == 0]
            if periodic_attempts:
                record, path, digest = periodic_attempts[-1]
            elif exact_attempts:
                record, path, digest = exact_attempts[-1]
            else:
                record, path, digest = max(
                    attempts,
                    key=lambda item: item[0]["periodic_z3"]["exact_multicover_nodes"],
                )
            detail = record["periodic_z3"]
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
                assert detail["exact_multicover_nodes"] > 0
            receipts.append({
                "path": f"{path.parent.name}/{path.name}",
                "sha256": digest,
                "attempts": [{
                    "path": f"{attempt_path.parent.name}/{attempt_path.name}",
                    "sha256": attempt_digest,
                    "solver_unknown": attempt_record["periodic_z3"]["solver_unknown"],
                    "exact_multicover_nodes": attempt_record["periodic_z3"]["exact_multicover_nodes"],
                } for attempt_record, attempt_path, attempt_digest in attempts],
                "orbit_range": [orbit, orbit + 1],
                "solver_unknown": detail["solver_unknown"],
                "exact_multicover_nodes": detail["exact_multicover_nodes"],
                "milliseconds": detail["milliseconds"],
            })
            rows.append(detail)
            selected_records.append(record)
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
        "exact_node_limits_per_orbit": [args.exact_node_limit, *args.retry_node_limit],
        "classification": "periodic" if positives else "bounded_inconclusive",
        "periodic_certificates": positives,
        "candidates": candidates,
        "campaign_receipt_sha256": campaign_digest.hexdigest(),
        "claim_scope": f"fixed_{args.copies}_copy_weighted_hnf_quotients",
    }
    if args.probe_dir:
        assert args.probe_solver and args.probe_timeout_ms > 0
        complete_probes = []
        partial_probes = []
        for path in sorted(Path(args.probe_dir).glob("*.ndjson")):
            payload = path.read_bytes()
            records = [json.loads(line) for line in payload.splitlines() if line.strip()]
            assert len(records) == 1
            record = records[0]
            detail = record["periodic_z3"]
            target = complete_probes if detail["milliseconds"] >= args.probe_timeout_ms else partial_probes
            target.append(record)
            if target is complete_probes:
                digest = hashlib.sha256(payload).hexdigest()
                campaign_digest.update(f"probe/{path.name}:{digest}\n".encode())
        result["solver_probe"] = {
            "solver": args.probe_solver,
            "timeout_ms_per_orbit": args.probe_timeout_ms,
            "completed_shards": len(complete_probes),
            "partial_interrupted_receipts_excluded": len(partial_probes),
            "periodic_certificates": sum(
                record["classification"] == "periodic" for record in complete_probes
            ),
            "exact_negative_orbits": sum(
                record["classification"] == "unresolved"
                and record["periodic_z3"]["solver_unknown"] == 0
                for record in complete_probes
            ),
            "solver_unknown_shards": sum(
                record["periodic_z3"]["solver_unknown"] for record in complete_probes
            ),
        }
        result["campaign_receipt_sha256"] = campaign_digest.hexdigest()
    if args.receipt_archive:
        archive_payload = "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in selected_records
        ).encode()
        archive_path = Path(args.receipt_archive)
        with gzip.GzipFile(filename=str(archive_path), mode="wb", mtime=0) as archive:
            archive.write(archive_payload)
        result["strongest_receipt_archive"] = str(archive_path)
        result["strongest_receipt_archive_sha256"] = hashlib.sha256(archive_payload).hexdigest()
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
