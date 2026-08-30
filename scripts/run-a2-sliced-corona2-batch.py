#!/usr/bin/env python3
"""Resume and parallelize exact radius-two A2-sliced CEGAR searches."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCREEN = ROOT / "scripts" / "screen-a2-layered-corona2-core-cegar.py"


def read_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_one(path: Path) -> dict:
    records = read_records(path)
    if len(records) != 1:
        raise ValueError(f"expected one record in {path}")
    return records[0]


def shard_path(output_dir: Path, candidate_id: str) -> Path:
    return output_dir / f"{candidate_id}.ndjson"


def checkpoint_path(checkpoint_dir: Path, candidate_id: str) -> Path:
    # The underlying screen derives this name from the stable shard stem.
    return checkpoint_dir / f"{candidate_id}.{candidate_id}.checkpoint.ndjson"


def terminal_record(record: dict) -> bool:
    classification = record.get("corona2_core_classification")
    detail = record.get("corona2_core_cegar", {})
    if classification == "radius2_witness":
        return detail.get("replay", {}).get("verified") is True
    if classification == "radius2_obstruction_z3":
        return detail.get("outer_exhausted") is True
    return False


def resumable_record(record: dict, allow_in_progress: bool = False) -> bool:
    detail = record.get("corona2_core_cegar", {})
    stopped_by = {"round_limit", "solver_timeout"}
    if allow_in_progress:
        stopped_by.add("in_progress")
    return (
        record.get("corona2_core_classification") == "unresolved"
        and detail.get("outer_exhausted") is False
        and isinstance(detail.get("clauses"), list)
        and detail.get("stopped_by") in stopped_by
    )


def valid_shard(path: Path, candidate_id: str, require_terminal: bool = False) -> bool:
    if not path.exists():
        return False
    try:
        record = read_one(path)
        if record.get("id") != candidate_id:
            return False
        if record.get("corona2_core_classification") == "unresolved":
            return resumable_record(record) and not require_terminal
        return terminal_record(record)
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def best_seed_path(shard: Path, checkpoint: Path, candidate_id: str) -> Path | None:
    candidates = []
    for path in (shard, checkpoint):
        if not path.exists():
            continue
        try:
            record = read_one(path)
        except (ValueError, json.JSONDecodeError):
            continue
        if record.get("id") != candidate_id or not (
            terminal_record(record) or resumable_record(record, allow_in_progress=True)
        ):
            continue
        detail = record["corona2_core_cegar"]
        candidates.append((
            int(detail.get("rounds", 0)),
            int(detail.get("cumulative_milliseconds", detail.get("milliseconds", 0))),
            path,
        ))
    return max(candidates, default=(0, 0, None))[2]


def run_task(task: dict) -> dict:
    output = Path(task["output"])
    checkpoint = Path(task["checkpoint"])
    seed = best_seed_path(output, checkpoint, task["id"])
    command = [
        sys.executable,
        str(SCREEN),
        "--input", task["input"],
        "--output", str(output),
        "--ids", task["id"],
        "--rounds", str(task["rounds"]),
        "--timeout-ms", str(task["timeout_ms"]),
        "--checkpoint-dir", task["checkpoint_dir"],
        "--outer-solver", task["outer_solver"],
        "--inner-solver", task["inner_solver"],
    ]
    if task["max_first_copies"] > 0:
        command.extend(("--max-first-copies", str(task["max_first_copies"])))
    if seed is not None:
        command.extend(("--seed-core", str(seed), "--only-seeded"))
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0 or not valid_shard(output, task["id"]):
        return {
            **task,
            "status": "failed",
            "stderr": completed.stderr[-2000:],
            "stdout": completed.stdout[-2000:],
        }
    record = read_one(output)
    detail = record["corona2_core_cegar"]
    return {
        **task,
        "status": record["corona2_core_classification"],
        "rounds": detail.get("rounds", 0),
        "clauses": len(detail.get("clauses", [])),
        "cumulative_milliseconds": detail.get(
            "cumulative_milliseconds", detail.get("milliseconds", 0)
        ),
        "stopped_by": detail.get("stopped_by"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merged-output", required=True)
    parser.add_argument("--candidate-ids", default="")
    parser.add_argument("--rounds", type=int, default=128,
                        help="additional CEGAR rounds per continuation")
    parser.add_argument("--timeout-ms", type=int, default=30000,
                        help="per outer or inner solver call")
    parser.add_argument("--max-first-copies", type=int, default=0)
    parser.add_argument("--outer-solver", choices=("z3", "qffd"), default="qffd")
    parser.add_argument("--inner-solver", choices=("z3", "qffd"), default="qffd")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-tasks", type=int, default=0)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    checkpoint_dir = output_dir / "checkpoints"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    requested = {value for value in args.candidate_ids.split(",") if value}
    records = [
        record for record in read_records(input_path)
        if record.get("corona_classification") == "root_corona_exists"
        and record.get("corona_z3", {}).get("replay", {}).get("verified") is True
        and (not requested or record.get("id") in requested)
    ]
    if requested and requested != {record["id"] for record in records}:
        missing = sorted(requested - {record["id"] for record in records})
        parser.error(f"candidate IDs lack replayed first coronas: {missing}")

    tasks = []
    for record in records:
        candidate_id = record["id"]
        output = shard_path(output_dir, candidate_id)
        if valid_shard(output, candidate_id, require_terminal=True):
            continue
        tasks.append({
            "id": candidate_id,
            "input": str(input_path),
            "output": str(output),
            "checkpoint": str(checkpoint_path(checkpoint_dir, candidate_id)),
            "checkpoint_dir": str(checkpoint_dir),
            "rounds": max(1, args.rounds),
            "timeout_ms": max(1, args.timeout_ms),
            "max_first_copies": max(0, args.max_first_copies),
            "outer_solver": args.outer_solver,
            "inner_solver": args.inner_solver,
        })
    if args.max_tasks > 0:
        tasks = tasks[:args.max_tasks]

    outcomes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run_task, task) for task in tasks]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            outcome = future.result()
            outcomes.append(outcome)
            print(json.dumps({
                "completed": completed,
                "scheduled": len(tasks),
                "id": outcome["id"],
                "status": outcome["status"],
                "rounds": outcome.get("rounds"),
                "clauses": outcome.get("clauses"),
                "cumulative_milliseconds": outcome.get("cumulative_milliseconds"),
                "stopped_by": outcome.get("stopped_by"),
            }, separators=(",", ":")), flush=True)

    merged = []
    missing = []
    for record in records:
        path = shard_path(output_dir, record["id"])
        if valid_shard(path, record["id"]):
            merged.append(read_one(path))
        else:
            missing.append(record["id"])
    Path(args.merged_output).write_text("".join(
        json.dumps(record, separators=(",", ":")) + "\n" for record in merged
    ))
    counts = Counter(record["corona2_core_classification"] for record in merged)
    failed = [outcome for outcome in outcomes if outcome["status"] == "failed"]
    print(json.dumps({
        "requested_candidates": len(records),
        "scheduled_tasks": len(tasks),
        "merged_candidates": len(merged),
        "classifications": dict(sorted(counts.items())),
        "terminal_candidates": sum(terminal_record(record) for record in merged),
        "missing_candidates": missing,
        "failed_tasks": len(failed),
        "merged_output": args.merged_output,
    }, indent=2), flush=True)
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
