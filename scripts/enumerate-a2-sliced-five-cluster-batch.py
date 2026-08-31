#!/usr/bin/env python3
"""Parallel, resumable compact census of connected five-copy A2 metatiles."""

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
    "a2_sliced_five_cluster",
    ROOT / "scripts" / "screen-a2-sliced-five-cluster-substitution.py",
)
FIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIVE)
TWO = FIVE.TWO


def digest_keys(keys) -> str:
    return hashlib.sha256(json.dumps(
        keys, separators=(",", ":")
    ).encode()).hexdigest()


def numeric_sort_key(canonical_key) -> bytes:
    """Encode tuple ordering as a fixed-width SQLite BLOB."""
    encoded = bytearray()
    for cell in canonical_key:
        for coordinate in cell[:3]:
            encoded.extend((int(coordinate) + (1 << 63)).to_bytes(8, "big"))
        encoded.extend(str(cell[3]).encode("ascii"))
        encoded.append(0)
    return bytes(encoded)


def shard_path(output_dir: Path, candidate_id: str, start: int, stop: int) -> Path:
    return output_dir / f"{candidate_id}-four-parents{start:05d}-{stop:05d}.json"


def valid_shard(path: Path, candidate_id: str, include_reflections: bool,
                start: int, stop: int, parent_total: int) -> bool:
    if not path.exists():
        return False
    try:
        receipt = json.loads(path.read_text())
        keys = receipt["canonical_keys"]
        return (
            receipt["id"] == candidate_id
            and receipt["include_reflections"] is include_reflections
            and receipt["copies"] == 5
            and receipt["four_copy_parent_total"] == parent_total
            and receipt["four_copy_parent_range"] == [start, stop]
            and receipt["symmetry_distinct_metatiles"] == len(keys)
            and receipt["canonical_sha256"] == digest_keys(keys)
            and keys == sorted(keys)
        )
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def enumerate_worker(task: dict) -> dict:
    records = TWO.read_ndjson(Path(task["input"]))
    record = next((item for item in records if item["id"] == task["id"]), None)
    if record is None:
        raise ValueError("candidate disappeared from census input")
    enumerated = FIVE.enumerate_five_copy_metatiles(
        record, Path(task["four_cache"]), task["include_reflections"],
        task["start"], task["stop"],
    )
    keys = [item["canonical_key"] for item in enumerated["metatiles"]]
    receipt = {
        "id": task["id"],
        "include_reflections": task["include_reflections"],
        "copies": 5,
        "raw_connected_extensions": enumerated["raw_connected_extensions"],
        "symmetry_distinct_metatiles": len(keys),
        "canonical_sha256": digest_keys(keys),
        "four_copy_parent_total": enumerated["four_copy_parent_total"],
        "four_copy_parent_range": enumerated["four_copy_parent_range"],
        "canonical_keys": keys,
    }
    output = Path(task["output"])
    temporary = output.with_suffix(f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(receipt, separators=(",", ":")))
    os.replace(temporary, output)
    return {
        "start": task["start"], "stop": task["stop"],
        "raw": receipt["raw_connected_extensions"], "types": len(keys),
    }


def run_subprocess_worker(task: dict) -> dict:
    command = [
        sys.executable, str(Path(__file__).resolve()),
        "--input", task["input"],
        "--output-dir", str(Path(task["output"]).parent),
        "--sqlite-cache", task["sqlite_cache"],
        "--four-cache", task["four_cache"],
        "--candidate-id", task["id"],
        "--four-parent-total", str(task["parent_total"]),
        "--worker-start", str(task["start"]),
        "--worker-stop", str(task["stop"]),
        "--worker-output", task["output"],
    ]
    if task["include_reflections"]:
        command.append("--include-reflections")
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr[-4000:] or completed.stdout[-4000:])
    return json.loads(completed.stdout.splitlines()[-1])


def merge_to_compact_sqlite(paths: list[Path], output: Path,
                            candidate_id: str, include_reflections: bool,
                            parent_total: int) -> dict:
    temporary = output.with_suffix(f".tmp-{os.getpid()}.sqlite")
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute(
        "CREATE TABLE representatives (sort_key BLOB PRIMARY KEY, "
        "key_json TEXT NOT NULL) WITHOUT ROWID"
    )
    raw = 0
    cursor = 0
    receipts = []
    try:
        for path in paths:
            receipt = json.loads(path.read_text())
            start, stop = receipt["four_copy_parent_range"]
            if start != cursor:
                raise ValueError(f"four-copy parent gap before {path}: {cursor} != {start}")
            if not valid_shard(
                path, candidate_id, include_reflections, start, stop, parent_total
            ):
                raise ValueError(f"invalid five-copy shard: {path}")
            cursor = stop
            raw += receipt["raw_connected_extensions"]
            receipts.append({
                "path": path.name,
                "four_copy_parent_range": [start, stop],
                "partial_types": receipt["symmetry_distinct_metatiles"],
                "canonical_sha256": receipt["canonical_sha256"],
            })
            connection.executemany(
                "INSERT OR IGNORE INTO representatives(sort_key,key_json) VALUES(?,?)",
                ((numeric_sort_key(key), json.dumps(key, separators=(",", ":")))
                 for key in receipt["canonical_keys"]),
            )
            connection.commit()
        if cursor != parent_total:
            raise ValueError(f"incomplete four-copy parent cover [0,{cursor}) of {parent_total}")
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
        connection.execute(
            "CREATE TABLE metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL) WITHOUT ROWID"
        )
        metadata = {
            "id": candidate_id,
            "include_reflections": include_reflections,
            "copies": 5,
            "cache_schema": "compact_canonical_alcove_keys_v2",
            "raw_connected_extensions": raw,
            "symmetry_distinct_metatiles": count,
            "canonical_sha256": canonical_sha256,
            "four_copy_parent_total": parent_total,
            "four_copy_parent_range": [0, parent_total],
            "range_receipts": receipts,
        }
        connection.executemany(
            "INSERT INTO metadata(key,value_json) VALUES(?,?)",
            ((key, json.dumps(value, separators=(",", ":")))
             for key, value in metadata.items()),
        )
        connection.commit()
        connection.close()
        output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temporary, output)
        return {
            "candidate": candidate_id, "complete": True, "types": count,
            "raw_connected_extensions": raw,
            "canonical_sha256": canonical_sha256,
            "sqlite_cache": str(output),
        }
    finally:
        connection.close()
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sqlite-cache", required=True)
    parser.add_argument("--four-cache", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--four-parent-total", type=int, required=True)
    parser.add_argument("--four-parent-span", type=int, default=25)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-tasks", type=int, default=0)
    parser.add_argument("--merge-existing", action="store_true")
    parser.add_argument("--delete-shards", action="store_true")
    parser.add_argument("--worker-start", type=int, default=-1, help=argparse.SUPPRESS)
    parser.add_argument("--worker-stop", type=int, default=-1, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", default="", help=argparse.SUPPRESS)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    records = TWO.read_ndjson(input_path)
    record = next((item for item in records if item["id"] == args.candidate_id), None)
    if record is None:
        parser.error("candidate ID is absent from input")
    four = FIVE.FOUR.cached_enumeration(
        record, args.include_reflections, Path(args.four_cache)
    )
    if len(four["metatiles"]) != args.four_parent_total:
        parser.error("four-copy cache count does not match --four-parent-total")
    if args.worker_start >= 0:
        result = enumerate_worker({
            "input": str(input_path), "output": args.worker_output,
            "four_cache": str(Path(args.four_cache).resolve()),
            "id": args.candidate_id,
            "include_reflections": args.include_reflections,
            "start": args.worker_start, "stop": args.worker_stop,
        })
        print(json.dumps(result, separators=(",", ":")), flush=True)
        return

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    span = max(1, args.four_parent_span)
    paths = []
    tasks = []
    for start in range(0, args.four_parent_total, span):
        stop = min(args.four_parent_total, start + span)
        path = shard_path(output_dir, args.candidate_id, start, stop)
        paths.append(path)
        if not args.merge_existing and not valid_shard(
            path, args.candidate_id, args.include_reflections,
            start, stop, args.four_parent_total,
        ):
            tasks.append({
                "input": str(input_path), "output": str(path),
                "sqlite_cache": str(Path(args.sqlite_cache).resolve()),
                "four_cache": str(Path(args.four_cache).resolve()),
                "id": args.candidate_id,
                "include_reflections": args.include_reflections,
                "parent_total": args.four_parent_total,
                "start": start, "stop": stop,
            })
    if args.max_tasks > 0:
        tasks = tasks[:args.max_tasks]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(run_subprocess_worker, task) for task in tasks]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            print(json.dumps({
                "completed": completed, "scheduled": len(tasks),
                "four_parent_range": [result["start"], result["stop"]],
                "raw": result["raw"], "partial_types": result["types"],
            }, separators=(",", ":")), flush=True)

    # The merge revalidates every identity, range, sorted key list, and digest.
    # Avoid parsing the full shard corpus twice merely to decide whether every
    # expected pathname is present.
    complete = all(path.exists() for path in paths)
    if not complete:
        print(json.dumps({
            "candidate": args.candidate_id, "complete": False,
            "completed_shards": sum(path.exists() for path in paths),
            "total_shards": len(paths),
        }, indent=2))
        return
    result = merge_to_compact_sqlite(
        paths, Path(args.sqlite_cache), args.candidate_id,
        args.include_reflections, args.four_parent_total,
    )
    print(json.dumps(result, indent=2), flush=True)
    if args.delete_shards:
        for path in paths:
            path.unlink()


if __name__ == "__main__":
    main()
