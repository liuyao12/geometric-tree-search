#!/usr/bin/env python3
"""Parallel, resumable proof screen for a large five-copy metatile cache."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
KINDS = (
    "atomic_local_obstruction", "local_obstruction", "exact_unsat",
    "mixed_metatile_rule", "unresolved",
)


def shard_path(output_dir: Path, candidate_id: str, start: int, stop: int) -> Path:
    return output_dir / f"{candidate_id}-five-parents{start:07d}-{stop:07d}.ndjson"


def replay_verified(result: dict) -> bool:
    kind = result["classification"]
    if kind == "atomic_local_obstruction":
        return result["atomic_local_obstruction_replay"]["verified"] is True
    if kind == "local_obstruction":
        return result["local_obstruction_replay"]["verified"] is True
    if kind == "exact_unsat":
        return result["exact_unsat_replay"]["verified"] is True
    if kind == "mixed_metatile_rule":
        return result["replay"]["verified"] is True
    return kind == "unresolved"


def load_valid_shard(path: Path, candidate_id: str, start: int, stop: int,
                     parent_total: int) -> dict:
    record = json.loads(path.read_text())
    detail = record["five_copy_alcove_metatile_screen"]
    results = detail["parent_results"]
    if (record["id"] != candidate_id
            or detail["symmetry_distinct_metatiles"] != parent_total
            or detail["parent_range"] != [start, stop]
            or detail["parents_completed"] != stop - start
            or len(results) != stop - start
            or any(result["parent_index"] != start + offset
                   for offset, result in enumerate(results))
            or any(not replay_verified(result) for result in results)
            or any(detail["parent_counts"].get(kind, 0) != sum(
                result["classification"] == kind for result in results
            ) for kind in KINDS)):
        raise ValueError(f"invalid five-copy screen shard: {path}")
    return record


def valid_shard(path: Path, candidate_id: str, start: int, stop: int,
                parent_total: int) -> bool:
    if not path.exists():
        return False
    try:
        load_valid_shard(path, candidate_id, start, stop, parent_total)
        return True
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def run_task(task: dict) -> dict:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "screen-a2-sliced-five-cluster-substitution.py"),
        "--input", task["input"],
        "--output", task["output"],
        "--enumeration-cache", task["four_cache"],
        "--five-enumeration-cache", task["five_cache"],
        "--ids", task["id"],
        "--scale", str(task["scale"]),
        "--timeout-ms", str(task["timeout_ms"]),
        "--parent-start", str(task["start"]),
        "--parent-stop", str(task["stop"]),
    ]
    if task["include_reflections"]:
        command.append("--include-reflections")
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr[-4000:] or completed.stdout[-4000:])
    record = load_valid_shard(
        Path(task["output"]), task["id"], task["start"], task["stop"],
        task["parent_total"],
    )
    return {
        "start": task["start"], "stop": task["stop"],
        "counts": record["five_copy_alcove_metatile_screen"]["parent_counts"],
    }


def closed_rule_alphabet(rules: dict[int, dict]):
    closed = None
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
        if valid and (closed is None or len(closure) < len(closed)):
            closed = sorted(closure)
    return closed


def merge_shards(paths: list[Path], output: Path, summary_output: Path,
                 candidate_id: str, parent_total: int, scale: int) -> dict:
    records = []
    cursor = 0
    counts = {kind: 0 for kind in KINDS}
    rules = {}
    reference = None
    receipts = []
    for path in paths:
        name = path.name
        start = int(name.split("-five-parents", 1)[1].split("-", 1)[0])
        stop = int(name.rsplit("-", 1)[1].split(".", 1)[0])
        if start != cursor:
            raise ValueError(f"parent gap before {path}: {cursor} != {start}")
        record = load_valid_shard(path, candidate_id, start, stop, parent_total)
        detail = record["five_copy_alcove_metatile_screen"]
        identity = {key: detail[key] for key in (
            "scale", "include_reflections", "family",
            "raw_connected_extensions", "symmetry_distinct_metatiles",
            "canonical_sha256", "four_copy_parent_total",
        )}
        if reference is None:
            reference = identity
        elif identity != reference:
            raise ValueError(f"five-copy cache identity changed in {path}")
        for kind in KINDS:
            counts[kind] += detail["parent_counts"].get(kind, 0)
        for result in detail["parent_results"]:
            if result["classification"] == "mixed_metatile_rule":
                rules[result["parent_index"]] = result
        receipts.append({
            "path": name, "parent_range": [start, stop],
            "parent_counts": detail["parent_counts"],
        })
        records.append(record)
        cursor = stop
    if cursor != parent_total or reference["scale"] != scale:
        raise ValueError("five-copy screen does not cover the requested alphabet")
    closed = closed_rule_alphabet(rules)
    if closed is not None:
        classification = "five_copy_metatile_substitution_system"
        certified = True
    elif not rules and counts["unresolved"] == 0:
        classification = f"no_five_copy_metatile_scalar{scale}_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    detail_prefix = {
        "certified": certified,
        **reference,
        "oriented_metatile_types": None,
        "oriented_alphabet_deferred": True,
        "parent_range": [0, parent_total],
        "parents_completed": parent_total,
        "closed_alphabet": closed,
        "parent_counts": counts,
        "range_receipts": receipts,
    }
    prefix = {
        "id": candidate_id,
        "classification": classification,
        "five_copy_alcove_metatile_screen": detail_prefix,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(f".tmp-{os.getpid()}.gz")
    result_digest = hashlib.sha256()
    with gzip.open(temporary, "wt", encoding="utf-8", compresslevel=9) as stream:
        serialized = json.dumps(prefix, separators=(",", ":"))
        stream.write(serialized[:-2])
        stream.write(',"parent_results":[')
        emitted = 0
        for record in records:
            for result in record["five_copy_alcove_metatile_screen"]["parent_results"]:
                encoded = json.dumps(result, separators=(",", ":"))
                if emitted:
                    stream.write(",")
                    result_digest.update(b",")
                stream.write(encoded)
                result_digest.update(encoded.encode())
                emitted += 1
        stream.write("]}}\n")
    if emitted != parent_total:
        temporary.unlink(missing_ok=True)
        raise ValueError("merged parent result count changed while writing")
    os.replace(temporary, output)
    archive_sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    summary = {
        "id": candidate_id,
        "classification": classification,
        "certified": certified,
        "scale": scale,
        "include_reflections": reference["include_reflections"],
        "family": reference["family"],
        "four_copy_parent_total": reference["four_copy_parent_total"],
        "raw_connected_extensions": reference["raw_connected_extensions"],
        "symmetry_distinct_metatiles": parent_total,
        "canonical_sha256": reference["canonical_sha256"],
        "parents_completed": parent_total,
        "parent_counts": counts,
        "closed_alphabet": closed,
        "all_parent_replays_verified": all(
            replay_verified(result)
            for record in records
            for result in record["five_copy_alcove_metatile_screen"]["parent_results"]
        ),
        "parent_results_sha256": result_digest.hexdigest(),
        "archive": output.name,
        "archive_sha256": archive_sha256,
        "range_receipts": receipts,
    }
    summary_output.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--four-cache", required=True)
    parser.add_argument("--five-cache", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merged-output", required=True)
    parser.add_argument("--summary-output", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--parent-total", type=int, required=True)
    parser.add_argument("--parent-span", type=int, default=50000)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--merge-existing", action="store_true")
    parser.add_argument("--delete-shards", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    tasks = []
    span = max(1, args.parent_span)
    for start in range(0, args.parent_total, span):
        stop = min(args.parent_total, start + span)
        path = shard_path(output_dir, args.candidate_id, start, stop)
        paths.append(path)
        if not args.merge_existing and not valid_shard(
            path, args.candidate_id, start, stop, args.parent_total
        ):
            tasks.append({
                "input": str(Path(args.input).resolve()),
                "output": str(path),
                "four_cache": str(Path(args.four_cache).resolve()),
                "five_cache": str(Path(args.five_cache).resolve()),
                "id": args.candidate_id,
                "parent_total": args.parent_total,
                "start": start, "stop": stop, "scale": args.scale,
                "timeout_ms": args.timeout_ms,
                "include_reflections": args.include_reflections,
            })
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run_task, task) for task in tasks]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            print(json.dumps({
                "completed": completed, "scheduled": len(tasks),
                "parent_range": [result["start"], result["stop"]],
                "parent_counts": result["counts"],
            }, separators=(",", ":")), flush=True)
    if not all(path.exists() for path in paths):
        print(json.dumps({
            "candidate": args.candidate_id, "complete": False,
            "completed_shards": sum(path.exists() for path in paths),
            "total_shards": len(paths),
        }, indent=2))
        return
    summary = merge_shards(
        paths, Path(args.merged_output), Path(args.summary_output),
        args.candidate_id, args.parent_total, args.scale,
    )
    print(json.dumps(summary, indent=2), flush=True)
    if args.delete_shards:
        for path in paths:
            path.unlink()


if __name__ == "__main__":
    main()
