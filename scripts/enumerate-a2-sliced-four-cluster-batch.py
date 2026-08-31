#!/usr/bin/env python3
"""Parallel, resumable canonical census of connected four-copy A2 metatiles."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_four_cluster",
    ROOT / "scripts" / "screen-a2-sliced-four-cluster-substitution.py",
)
FOUR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FOUR)


def read_one(path: Path) -> dict:
    return json.loads(path.read_text())


def shard_path(output_dir: Path, candidate_id: str, start: int, stop: int) -> Path:
    return output_dir / f"{candidate_id}-three-parents{start:05d}-{stop:05d}.json"


def enumeration_digest(metatiles: list[dict]) -> str:
    return hashlib.sha256(json.dumps(
        [item["canonical_key"] for item in metatiles], separators=(",", ":")
    ).encode()).hexdigest()


def valid_shard(path: Path, candidate_id: str, include_reflections: bool,
                start: int, stop: int, parent_total: int) -> bool:
    if not path.exists():
        return False
    try:
        receipt = read_one(path)
        enumerated = receipt["enumerated"]
        metatiles = enumerated["metatiles"]
        return (
            receipt["id"] == candidate_id
            and receipt["include_reflections"] is include_reflections
            and receipt["copies"] == 4
            and enumerated["three_copy_parent_total"] == parent_total
            and enumerated["three_copy_parent_range"] == [start, stop]
            and enumerated["symmetry_distinct_metatiles"] == len(metatiles)
            and enumerated["canonical_sha256"] == enumeration_digest(metatiles)
        )
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def enumerate_task(task: dict) -> dict:
    records = [
        json.loads(line) for line in Path(task["input"]).read_text().splitlines()
        if line.strip()
    ]
    record = records[task["candidate_index"]]
    if record["id"] != task["id"]:
        raise ValueError("candidate identity changed while enumerating")
    enumerated = FOUR.enumerate_four_copy_metatiles(
        record,
        task["include_reflections"],
        task["start"],
        task["stop"],
    )
    output = Path(task["output"])
    temporary = output.with_suffix(f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps({
        "id": task["id"],
        "include_reflections": task["include_reflections"],
        "copies": 4,
        "enumerated": enumerated,
    }, separators=(",", ":")))
    os.replace(temporary, output)
    return {
        "start": task["start"],
        "stop": task["stop"],
        "raw": enumerated["raw_connected_extensions"],
        "types": enumerated["symmetry_distinct_metatiles"],
    }


def run_subprocess_task(task: dict) -> dict:
    command = [
        sys.executable, str(Path(__file__).resolve()),
        "--input", task["input"],
        "--output-dir", str(Path(task["output"]).parent),
        "--merged-cache", task["output"],
        "--candidate-index", str(task["candidate_index"]),
        "--candidate-id", task["id"],
        "--three-parent-total", str(task["parent_total"]),
        "--worker-start", str(task["start"]),
        "--worker-stop", str(task["stop"]),
        "--worker-output", task["output"],
    ]
    if task["include_reflections"]:
        command.append("--include-reflections")
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr[-2000:] or completed.stdout[-2000:])
    return json.loads(completed.stdout.splitlines()[-1])


def merge_shards(paths: list[Path], candidate_id: str,
                 include_reflections: bool, parent_total: int) -> dict:
    representatives = {}
    raw = 0
    receipts = []
    cursor = 0
    for path in paths:
        receipt = read_one(path)
        enumerated = receipt["enumerated"]
        start, stop = enumerated["three_copy_parent_range"]
        if start != cursor:
            raise ValueError(f"three-copy parent gap before {path}: {cursor} != {start}")
        cursor = stop
        raw += enumerated["raw_connected_extensions"]
        receipts.append({
            "path": path.name,
            "three_copy_parent_range": [start, stop],
            "partial_types": enumerated["symmetry_distinct_metatiles"],
            "canonical_sha256": enumerated["canonical_sha256"],
        })
        for metatile in enumerated["metatiles"]:
            key = tuple(tuple(cell) for cell in metatile["canonical_key"])
            representatives.setdefault(key, metatile)
    if cursor != parent_total:
        raise ValueError(f"incomplete three-copy parent cover [0, {cursor}) of {parent_total}")
    metatiles = [representatives[key] for key in sorted(representatives)]
    enumerated = {
        "raw_connected_extensions": raw,
        "symmetry_distinct_metatiles": len(metatiles),
        "canonical_sha256": enumeration_digest(metatiles),
        "three_copy_parent_total": parent_total,
        "three_copy_parent_range": [0, parent_total],
        "range_receipts": receipts,
        "metatiles": metatiles,
    }
    return {
        "id": candidate_id,
        "include_reflections": include_reflections,
        "copies": 4,
        "enumerated": enumerated,
    }


def numeric_sort_key(canonical_key: list[list]) -> bytes:
    """Encode Python's tuple ordering as a fixed-width SQLite BLOB key."""
    encoded = bytearray()
    for cell in canonical_key:
        for coordinate in cell[:3]:
            encoded.extend((int(coordinate) + (1 << 63)).to_bytes(8, "big"))
        encoded.extend(str(cell[3]).encode("ascii"))
        encoded.append(0)
    return bytes(encoded)


def merge_shards_to_cache(paths: list[Path], candidate_id: str,
                          include_reflections: bool, parent_total: int,
                          output: Path, sqlite_output: Path | None = None,
                          write_json: bool = True) -> dict:
    """Deduplicate a large census on disk and stream its canonical cache."""
    database = output.with_suffix(f".merge-{os.getpid()}.sqlite")
    database.unlink(missing_ok=True)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute("CREATE TABLE representatives (sort_key BLOB PRIMARY KEY, key_json TEXT, value_json TEXT) WITHOUT ROWID")
    raw = 0
    receipts = []
    cursor = 0
    try:
        for path in paths:
            receipt = read_one(path)
            enumerated = receipt["enumerated"]
            start, stop = enumerated["three_copy_parent_range"]
            if start != cursor:
                raise ValueError(f"three-copy parent gap before {path}: {cursor} != {start}")
            cursor = stop
            raw += enumerated["raw_connected_extensions"]
            receipts.append({
                "path": path.name,
                "three_copy_parent_range": [start, stop],
                "partial_types": enumerated["symmetry_distinct_metatiles"],
                "canonical_sha256": enumerated["canonical_sha256"],
            })
            connection.executemany(
                "INSERT OR IGNORE INTO representatives(sort_key,key_json,value_json) VALUES(?,?,?)",
                ((
                    numeric_sort_key(metatile["canonical_key"]),
                    json.dumps(metatile["canonical_key"], separators=(",", ":")),
                    json.dumps(metatile, separators=(",", ":")),
                ) for metatile in enumerated["metatiles"]),
            )
            connection.commit()
        if cursor != parent_total:
            raise ValueError(f"incomplete three-copy parent cover [0, {cursor}) of {parent_total}")
        count = connection.execute("SELECT COUNT(*) FROM representatives").fetchone()[0]
        digest = hashlib.sha256()
        digest.update(b"[")
        for index, (key_json,) in enumerate(connection.execute(
            "SELECT key_json FROM representatives ORDER BY sort_key"
        )):
            if index:
                digest.update(b",")
            digest.update(key_json.encode())
        digest.update(b"]")
        canonical_sha256 = digest.hexdigest()
        prefix = {
            "id": candidate_id,
            "include_reflections": include_reflections,
            "copies": 4,
            "enumerated": {
                "raw_connected_extensions": raw,
                "symmetry_distinct_metatiles": count,
                "canonical_sha256": canonical_sha256,
                "three_copy_parent_total": parent_total,
                "three_copy_parent_range": [0, parent_total],
                "range_receipts": receipts,
            },
        }
        if write_json:
            temporary = output.with_suffix(f".tmp-{os.getpid()}")
            serialized_prefix = json.dumps(prefix, separators=(",", ":"))
            with temporary.open("w") as stream:
                stream.write(serialized_prefix[:-2])
                stream.write(',"metatiles":[')
                for index, (value_json,) in enumerate(connection.execute(
                    "SELECT value_json FROM representatives ORDER BY sort_key"
                )):
                    if index:
                        stream.write(",")
                    stream.write(value_json)
                stream.write("]}}")
            os.replace(temporary, output)
        if sqlite_output is not None:
            connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL) WITHOUT ROWID")
            metadata = {
                "id": candidate_id,
                "include_reflections": include_reflections,
                "copies": 4,
                "raw_connected_extensions": raw,
                "symmetry_distinct_metatiles": count,
                "canonical_sha256": canonical_sha256,
                "three_copy_parent_total": parent_total,
                "three_copy_parent_range": [0, parent_total],
                "range_receipts": receipts,
            }
            connection.executemany(
                "INSERT INTO metadata(key,value_json) VALUES(?,?)",
                ((key, json.dumps(value, separators=(",", ":")))
                 for key, value in metadata.items()),
            )
            connection.commit()
            connection.close()
            sqlite_output.parent.mkdir(parents=True, exist_ok=True)
            os.replace(database, sqlite_output)
        return {
            "candidate": candidate_id,
            "complete": True,
            "types": count,
            "canonical_sha256": canonical_sha256,
            "merged_cache": str(output) if write_json else None,
            "sqlite_cache": str(sqlite_output) if sqlite_output is not None else None,
        }
    finally:
        connection.close()
        database.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merged-cache", required=True)
    parser.add_argument("--sqlite-cache")
    parser.add_argument("--sqlite-only", action="store_true")
    parser.add_argument("--candidate-index", type=int, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--three-parent-total", type=int, required=True)
    parser.add_argument("--three-parent-span", type=int, default=100)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-tasks", type=int, default=0)
    parser.add_argument("--worker-start", type=int, default=-1, help=argparse.SUPPRESS)
    parser.add_argument("--worker-stop", type=int, default=-1, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", default="", help=argparse.SUPPRESS)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    records = [json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    if not 0 <= args.candidate_index < len(records):
        parser.error("candidate index is out of range")
    if records[args.candidate_index]["id"] != args.candidate_id:
        parser.error("candidate ID does not match candidate index")
    if args.worker_start >= 0:
        if not args.worker_output or args.worker_stop <= args.worker_start:
            parser.error("invalid internal worker range")
        result = enumerate_task({
            "input": str(input_path),
            "output": args.worker_output,
            "candidate_index": args.candidate_index,
            "id": args.candidate_id,
            "include_reflections": args.include_reflections,
            "start": args.worker_start,
            "stop": args.worker_stop,
        })
        print(json.dumps(result, separators=(",", ":")), flush=True)
        return
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    span = max(1, args.three_parent_span)
    paths = []
    tasks = []
    for start in range(0, args.three_parent_total, span):
        stop = min(args.three_parent_total, start + span)
        path = shard_path(output_dir, args.candidate_id, start, stop)
        paths.append(path)
        if not valid_shard(
            path, args.candidate_id, args.include_reflections,
            start, stop, args.three_parent_total,
        ):
            tasks.append({
                "input": str(input_path),
                "output": str(path),
                "candidate_index": args.candidate_index,
                "id": args.candidate_id,
                "include_reflections": args.include_reflections,
                "parent_total": args.three_parent_total,
                "start": start,
                "stop": stop,
            })
    if args.max_tasks > 0:
        tasks = tasks[:args.max_tasks]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run_subprocess_task, task) for task in tasks]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            print(json.dumps({
                "completed": completed,
                "scheduled": len(tasks),
                "three_parent_range": [result["start"], result["stop"]],
                "raw": result["raw"],
                "partial_types": result["types"],
            }, separators=(",", ":")), flush=True)

    complete = all(valid_shard(
        path, args.candidate_id, args.include_reflections,
        start, min(args.three_parent_total, start + span), args.three_parent_total,
    ) for start, path in zip(range(0, args.three_parent_total, span), paths))
    if complete:
        output = Path(args.merged_cache)
        result = merge_shards_to_cache(
            paths, args.candidate_id, args.include_reflections,
            args.three_parent_total, output,
            Path(args.sqlite_cache) if args.sqlite_cache else None,
            not args.sqlite_only,
        )
        print(json.dumps(result, indent=2), flush=True)
    else:
        print(json.dumps({
            "candidate": args.candidate_id,
            "complete": False,
            "completed_shards": sum(path.exists() for path in paths),
            "total_shards": len(paths),
        }, indent=2), flush=True)


if __name__ == "__main__":
    main()
