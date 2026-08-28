#!/usr/bin/env python3
"""Resume, parallelize, and merge three-copy A2 substitution parent ranges."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCREEN = ROOT / "scripts" / "screen-a2-sliced-three-cluster-substitution.py"


def read_one(path: Path) -> dict:
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len(records) != 1:
        raise ValueError(f"expected one record in {path}")
    return records[0]


def shard_path(output_dir: Path, candidate_id: str, start: int, stop: int) -> Path:
    return output_dir / f"{candidate_id}-parents{start:04d}-{stop:04d}.ndjson"


def valid_shard(path: Path, candidate_id: str, start: int, stop: int,
                require_decided: bool = True) -> bool:
    if not path.exists():
        return False
    try:
        record = read_one(path)
        detail = record["three_copy_alcove_metatile_screen"]
        if record["id"] != candidate_id or detail["parent_range"] != [start, stop]:
            return False
        parents = detail["parent_results"]
        if detail["parents_completed"] != stop - start or len(parents) != stop - start:
            return False
        if [parent["parent_index"] for parent in parents] != list(range(start, stop)):
            return False
        if record["classification"] == "three_copy_metatile_substitution_system":
            return bool(detail.get("certified") and detail.get("closed_alphabet"))
        return not require_decided or all(
            parent["classification"] != "unresolved" for parent in parents
        )
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def run_task(task: dict) -> dict:
    output = Path(task["output"])
    temporary = output.with_suffix(f".tmp-{os.getpid()}")
    command = [
        sys.executable, str(SCREEN),
        "--input", task["input"],
        "--output", str(temporary),
        "--scale", str(task["scale"]),
        "--timeout-ms", str(task["timeout_ms"]),
        "--parent-start", str(task["start"]),
        "--parent-stop", str(task["stop"]),
        "--offset", str(task["candidate_index"]),
        "--limit", "1",
    ]
    if task["include_reflections"]:
        command.append("--include-reflections")
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        temporary.unlink(missing_ok=True)
        return {**task, "status": "failed", "stderr": completed.stderr[-2000:]}
    if not valid_shard(temporary, task["id"], task["start"], task["stop"], False):
        temporary.unlink(missing_ok=True)
        return {**task, "status": "invalid", "stderr": completed.stdout[-2000:]}
    os.replace(temporary, output)
    record = read_one(output)
    detail = record["three_copy_alcove_metatile_screen"]
    return {
        **task,
        "status": record["classification"],
        "counts": detail["parent_counts"],
    }


def closed_rule_alphabet(parent_results: list[dict]):
    rules = {
        result["parent_index"]: result
        for result in parent_results
        if result["classification"] == "mixed_metatile_rule"
    }
    best = None
    for seed in sorted(rules):
        closure = {seed}
        frontier = [seed]
        valid = True
        while frontier and valid:
            rule = rules.get(frontier.pop())
            if rule is None:
                valid = False
                break
            for child in rule["rule"]:
                child_index = child["type_index"]
                if child_index not in closure:
                    closure.add(child_index)
                    frontier.append(child_index)
        if valid and (best is None or len(closure) < len(best)):
            best = sorted(closure)
    return best


def merge_candidate(paths: list[Path], parent_total: int) -> dict:
    records = [read_one(path) for path in paths]
    details = [record["three_copy_alcove_metatile_screen"] for record in records]
    identity_fields = (
        "scale", "include_reflections", "family", "raw_connected_extensions",
        "symmetry_distinct_metatiles", "canonical_sha256", "oriented_metatile_types",
    )
    for field in identity_fields:
        if len({json.dumps(detail[field], sort_keys=True) for detail in details}) != 1:
            raise ValueError(f"inconsistent shard field {field}")
    ordered = sorted(zip(paths, records), key=lambda item: item[1][
        "three_copy_alcove_metatile_screen"]["parent_range"])
    cursor = 0
    parents = []
    receipts = []
    for path, record in ordered:
        detail = record["three_copy_alcove_metatile_screen"]
        start, stop = detail["parent_range"]
        if start != cursor or not start < stop <= parent_total:
            raise ValueError(f"parent range gap or overlap at {path}: {[start, stop]}")
        parents.extend(detail["parent_results"])
        receipts.append({"path": path.name, "parent_range": [start, stop]})
        cursor = stop
    if cursor != parent_total:
        raise ValueError(f"incomplete parent cover [0, {cursor}) of {parent_total}")
    unknowns = sum(parent["classification"] == "unresolved" for parent in parents)
    closed = closed_rule_alphabet(parents)
    if closed is not None:
        classification = "three_copy_metatile_substitution_system"
        certified = True
    elif not unknowns and not any(
        parent["classification"] == "mixed_metatile_rule" for parent in parents
    ):
        classification = f"no_three_copy_metatile_scalar{details[0]['scale']}_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    counts = {
        kind: sum(parent["classification"] == kind for parent in parents)
        for kind in ("atomic_local_obstruction", "local_obstruction", "exact_unsat",
                     "mixed_metatile_rule", "unresolved")
    }
    return {
        **records[0],
        "classification": classification,
        "three_copy_alcove_metatile_screen": {
            **{field: details[0][field] for field in identity_fields},
            "certified": certified,
            "parent_range": [0, parent_total],
            "parents_completed": parent_total,
            "closed_alphabet": closed,
            "parent_counts": counts,
            "parent_results": parents,
            "range_receipts": receipts,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merged-output", required=True)
    parser.add_argument("--candidate-index", type=int, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--parent-total", type=int, required=True)
    parser.add_argument("--parent-span", type=int, default=25)
    parser.add_argument("--scale", type=int, default=3)
    parser.add_argument("--timeout-ms", type=int, default=300000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-tasks", type=int, default=0)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    records = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    if not 0 <= args.candidate_index < len(records):
        parser.error("candidate index is out of range")
    if records[args.candidate_index]["id"] != args.candidate_id:
        parser.error("candidate ID does not match candidate index")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    tasks = []
    for start in range(0, args.parent_total, args.parent_span):
        stop = min(args.parent_total, start + args.parent_span)
        path = shard_path(output_dir, args.candidate_id, start, stop)
        paths.append(path)
        if not valid_shard(path, args.candidate_id, start, stop):
            tasks.append({
                "id": args.candidate_id,
                "candidate_index": args.candidate_index,
                "input": str(input_path),
                "output": str(path),
                "scale": args.scale,
                "timeout_ms": args.timeout_ms,
                "include_reflections": args.include_reflections,
                "start": start,
                "stop": stop,
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
                "parent_range": [outcome["start"], outcome["stop"]],
                "status": outcome["status"],
                "counts": outcome.get("counts"),
            }, separators=(",", ":")), flush=True)
    decided_paths = [
        path for start, path in zip(range(0, args.parent_total, args.parent_span), paths)
        if valid_shard(path, args.candidate_id, start,
                       min(args.parent_total, start + args.parent_span))
    ]
    merged = None
    if len(decided_paths) == len(paths):
        merged = merge_candidate(decided_paths, args.parent_total)
        Path(args.merged_output).write_text(json.dumps(merged, separators=(",", ":")) + "\n")
    failed = sum(outcome["status"] in ("failed", "invalid") for outcome in outcomes)
    print(json.dumps({
        "candidate": args.candidate_id,
        "scheduled_tasks": len(tasks),
        "decided_shards": len(decided_paths),
        "total_shards": len(paths),
        "merged_classification": merged and merged["classification"],
        "failed_tasks": failed,
    }, indent=2), flush=True)
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
