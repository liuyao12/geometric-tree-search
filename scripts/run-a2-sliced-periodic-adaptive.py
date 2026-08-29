#!/usr/bin/env python3
"""Adaptive exact A2 periodic screen that stops a candidate at its first witness."""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_periodic_batch",
    ROOT / "scripts" / "run-a2-sliced-periodic-batch.py",
)
BATCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BATCH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merged-output", required=True)
    parser.add_argument("--candidate-ids", required=True)
    parser.add_argument("--copies", type=int, default=12)
    parser.add_argument("--orbit-total", type=int, default=81)
    parser.add_argument("--orbit-span", type=int, default=9)
    parser.add_argument("--orbit-order", default="36,0,9,18,27,45,54,63,72")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--solver", choices=("qffd", "default"), default="qffd")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    records = [record for record in BATCH.read_ndjson(input_path)
               if record.get("classification") == "unresolved"]
    offsets = {record["id"]: index for index, record in enumerate(records)}
    requested = [item.strip() for item in args.candidate_ids.split(",") if item.strip()]
    missing = [candidate_id for candidate_id in requested if candidate_id not in offsets]
    if missing:
        parser.error(f"candidate IDs not found among unresolved rows: {missing}")

    natural_starts = list(range(0, args.orbit_total, args.orbit_span))
    preferred = [int(value) for value in args.orbit_order.split(",") if value.strip()]
    starts = [start for start in preferred if start in natural_starts]
    starts.extend(start for start in natural_starts if start not in starts)
    if sorted(starts) != natural_starts:
        parser.error("orbit order must cover each configured orbit band exactly once")

    active = set(requested)
    positives: dict[str, dict] = {}
    outcomes = []
    for start in starts:
        stop = min(args.orbit_total, start + args.orbit_span)
        tasks = []
        for candidate_id in sorted(active):
            path = BATCH.shard_path(output_dir, candidate_id, start, stop)
            if BATCH.valid_shard(path, candidate_id, start, stop):
                record = BATCH.read_ndjson(path)[0]
                if record["classification"] == "periodic":
                    positives[candidate_id] = record
                continue
            tasks.append({
                "id": candidate_id,
                "offset": offsets[candidate_id],
                "input": str(input_path),
                "output": str(path),
                "copies": args.copies,
                "solver": args.solver,
                "timeout_ms": args.timeout_ms,
                "start": start,
                "stop": stop,
            })
        active.difference_update(positives)
        if tasks:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max(1, args.workers)
            ) as pool:
                futures = [pool.submit(BATCH.run_task, task) for task in tasks]
                for future in concurrent.futures.as_completed(futures):
                    outcome = future.result()
                    outcomes.append(outcome)
                    print(json.dumps({
                        "id": outcome["id"],
                        "orbit_range": [outcome["start"], outcome["stop"]],
                        "status": outcome["status"],
                        "solver_unknown": outcome.get("solver_unknown"),
                        "milliseconds": outcome.get("milliseconds"),
                    }, separators=(",", ":")), flush=True)
                    if outcome["status"] == "periodic":
                        record = BATCH.read_ndjson(Path(outcome["output"]))[0]
                        positives[outcome["id"]] = record
            active.difference_update(positives)
        print(json.dumps({
            "completed_orbit_range": [start, stop],
            "periodic_so_far": len(positives),
            "active": len(active),
        }, separators=(",", ":")), flush=True)
        if not active:
            break

    merged = []
    incomplete = {}
    for candidate_id in requested:
        if candidate_id in positives:
            merged.append(positives[candidate_id])
            continue
        paths = [BATCH.shard_path(output_dir, candidate_id, start,
                                  min(args.orbit_total, start + args.orbit_span))
                 for start in natural_starts]
        decided = [path for path in paths if BATCH.valid_shard(
            path, candidate_id,
            int(path.stem.rsplit("orbits", 1)[1].split("-", 1)[0]),
            int(path.stem.rsplit("-", 1)[1]),
        )]
        if len(decided) != len(paths):
            incomplete[candidate_id] = {
                "decided_orbit_bands": len(decided),
                "total_orbit_bands": len(paths),
            }
            continue
        merged.append(BATCH.merge_candidate(candidate_id, paths, args.copies))

    Path(args.merged_output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    print(json.dumps({
        "requested_candidates": len(requested),
        "periodic": len(positives),
        "exact_negative": sum(record and record["classification"] == "unresolved"
                              for record in merged),
        "incomplete": incomplete,
        "merged_output": args.merged_output,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
