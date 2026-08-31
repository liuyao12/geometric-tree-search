#!/usr/bin/env python3
"""Resume and merge exact A2-sliced periodic-quotient orbit shards."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCREEN = ROOT / "scripts" / "screen-a2-layered-periodic-z3.py"
MERGE_SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_orbit_merge",
    ROOT / "scripts" / "merge-a2-layered-periodic-orbit-exact.py",
)
MERGE = importlib.util.module_from_spec(MERGE_SPEC)
MERGE_SPEC.loader.exec_module(MERGE)


def read_ndjson(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def shard_path(output_dir: Path, candidate_id: str, start: int, stop: int) -> Path:
    return output_dir / f"{candidate_id}-orbits{start:03d}-{stop:03d}.ndjson"


def valid_shard(path: Path, candidate_id: str, start: int, stop: int,
                require_decided: bool = True) -> bool:
    if not path.exists():
        return False
    try:
        records = read_ndjson(path)
        if len(records) != 1 or records[0]["id"] != candidate_id:
            return False
        screen = records[0]["periodic_z3"]
        if screen["hnf_range"] != [start, stop]:
            return False
        if records[0]["classification"] == "periodic":
            return bool(screen.get("replay", {}).get("verified"))
        structurally_complete = screen.get("stopped_by") is None \
            and screen.get("hnf_visited") == stop - start
        return structurally_complete and (
            not require_decided or screen.get("solver_unknown", 0) == 0
        )
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def run_task(task: dict) -> dict:
    output = Path(task["output"])
    positive_marker = Path(task["positive_marker"])
    if positive_marker.exists():
        return {**task, "status": "skipped_positive"}
    temporary = output.with_suffix(f".tmp-{os.getpid()}")
    command = [
        sys.executable,
        str(SCREEN),
        "--input", task["input"],
        "--output", str(temporary),
        "--min-copies", str(task["copies"]),
        "--max-copies", str(task["copies"]),
        "--solver", task["solver"],
        "--hnf-timeout-ms", str(task["timeout_ms"]),
        "--hnf-orbit-representatives",
        "--hnf-start", str(task["start"]),
        "--hnf-stop", str(task["stop"]),
        "--only-unresolved",
        "--offset", str(task["offset"]),
        "--limit", "1",
    ]
    if task.get("exact_node_limit"):
        command.extend(("--exact-node-limit", str(task["exact_node_limit"])))
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        temporary.unlink(missing_ok=True)
        return {**task, "status": "failed", "stderr": completed.stderr[-2000:]}
    if not valid_shard(temporary, task["id"], task["start"], task["stop"],
                       require_decided=False):
        temporary.unlink(missing_ok=True)
        return {**task, "status": "invalid", "stderr": completed.stdout[-2000:]}
    os.replace(temporary, output)
    record = read_ndjson(output)[0]
    if record["classification"] == "periodic":
        positive_marker.write_text(str(output) + "\n")
    return {
        **task,
        "status": record["classification"],
        "solver_unknown": record["periodic_z3"].get("solver_unknown", 0),
        "milliseconds": record["periodic_z3"].get("milliseconds", 0),
    }


def merge_candidate(candidate_id: str, paths: list[Path], copies: int) -> dict | None:
    records = [read_ndjson(path)[0] for path in paths]
    positives = [record for record in records if record["classification"] == "periodic"]
    if positives:
        positive = positives[0]
        if not positive["periodic_z3"]["replay"]["verified"]:
            raise ValueError(f"unverified positive shard for {candidate_id}")
        return positive
    if any(record["periodic_z3"].get("solver_unknown") for record in records):
        return None
    return MERGE.merge_records(records, copies)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merged-output", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--candidate-ids",
        help="comma-separated IDs from the unresolved input rows",
    )
    selection.add_argument(
        "--all-unresolved",
        action="store_true",
        help="screen every unresolved row in the input",
    )
    parser.add_argument("--copies", type=int, default=12)
    parser.add_argument("--orbit-total", type=int, default=81)
    parser.add_argument("--orbit-span", type=int, default=9)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--solver", choices=("exact", "qffd", "default"), default="qffd")
    parser.add_argument("--exact-node-limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-tasks", type=int, default=0)
    parser.add_argument(
        "--retry-unknown-from",
        help="schedule only orbit shards whose receipt in this directory has solver_unknown > 0",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    unresolved = [record for record in read_ndjson(input_path)
                  if record.get("classification") == "unresolved"]
    requested = (
        [record["id"] for record in unresolved]
        if args.all_unresolved
        else [item.strip() for item in args.candidate_ids.split(",") if item.strip()]
    )
    offsets = {record["id"]: index for index, record in enumerate(unresolved)}
    missing = [candidate_id for candidate_id in requested if candidate_id not in offsets]
    if missing:
        parser.error(f"candidate IDs not found among unresolved rows: {missing}")

    tasks = []
    retry_unknown_dir = Path(args.retry_unknown_from).resolve() if args.retry_unknown_from else None
    candidate_paths: dict[str, list[Path]] = {}
    for candidate_id in requested:
        paths = []
        for start in range(0, args.orbit_total, args.orbit_span):
            stop = min(args.orbit_total, start + args.orbit_span)
            path = shard_path(output_dir, candidate_id, start, stop)
            paths.append(path)
        positive_marker = output_dir / f"{candidate_id}.periodic"
        known_positive = next((
            path for path in paths
            if path.exists()
            and read_ndjson(path)[0].get("classification") == "periodic"
            and valid_shard(path, candidate_id,
                            read_ndjson(path)[0]["periodic_z3"]["hnf_range"][0],
                            read_ndjson(path)[0]["periodic_z3"]["hnf_range"][1])
        ), None)
        if known_positive is not None:
            positive_marker.write_text(str(known_positive) + "\n")
        else:
            positive_marker.unlink(missing_ok=True)
        for start, path in zip(range(0, args.orbit_total, args.orbit_span), paths):
            stop = min(args.orbit_total, start + args.orbit_span)
            if retry_unknown_dir is not None:
                prior_path = shard_path(retry_unknown_dir, candidate_id, start, stop)
                if not prior_path.exists():
                    continue
                prior = read_ndjson(prior_path)[0]
                if not prior["periodic_z3"].get("solver_unknown"):
                    continue
            if not valid_shard(path, candidate_id, start, stop):
                tasks.append({
                    "id": candidate_id,
                    "offset": offsets[candidate_id],
                    "input": str(input_path),
                    "output": str(path),
                    "copies": args.copies,
                    "solver": args.solver,
                    "timeout_ms": args.timeout_ms,
                    "exact_node_limit": args.exact_node_limit,
                    "start": start,
                    "stop": stop,
                    "positive_marker": str(positive_marker),
                })
        candidate_paths[candidate_id] = paths
    requested_rank = {candidate_id: index for index, candidate_id in enumerate(requested)}
    tasks.sort(key=lambda task: (
        task["start"], task["stop"], requested_rank[task["id"]]
    ))
    if args.max_tasks > 0:
        tasks = tasks[:args.max_tasks]

    outcomes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(run_task, task): task for task in tasks}
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            outcome = future.result()
            outcomes.append(outcome)
            print(json.dumps({
                "completed": completed,
                "scheduled": len(tasks),
                "id": outcome["id"],
                "orbit_range": [outcome["start"], outcome["stop"]],
                "status": outcome["status"],
                "solver_unknown": outcome.get("solver_unknown"),
                "milliseconds": outcome.get("milliseconds"),
            }, separators=(",", ":")), flush=True)

    merged = []
    incomplete = {}
    for candidate_id, paths in candidate_paths.items():
        present = [path for path in paths if path.exists()]
        positive = next((
            path for path in present
            if read_ndjson(path)[0].get("classification") == "periodic"
        ), None)
        if positive is not None:
            merged.append(read_ndjson(positive)[0])
            continue
        if len(present) != len(paths):
            incomplete[candidate_id] = {"present": len(present), "expected": len(paths)}
            continue
        result = merge_candidate(candidate_id, present, args.copies)
        if result is None:
            incomplete[candidate_id] = {"solver_unknown_shards": sum(
                bool(read_ndjson(path)[0]["periodic_z3"].get("solver_unknown"))
                for path in present
            )}
            continue
        merged.append(result)
    Path(args.merged_output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    failed = [outcome for outcome in outcomes if outcome["status"] in ("failed", "invalid")]
    print(json.dumps({
        "requested_candidates": len(requested),
        "scheduled_tasks": len(tasks),
        "merged_candidates": len(merged),
        "periodic": sum(record["classification"] == "periodic" for record in merged),
        "exact_negative": sum(record["classification"] == "unresolved" for record in merged),
        "incomplete": incomplete,
        "failed_tasks": len(failed),
        "merged_output": args.merged_output,
    }, indent=2), flush=True)
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
