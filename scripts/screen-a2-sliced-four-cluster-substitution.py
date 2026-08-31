#!/usr/bin/env python3
"""Exact mixed substitution screen for face-connected four-copy A2 metatiles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


THREE = load("a2_sliced_three_cluster", "screen-a2-sliced-three-cluster-substitution.py")
TWO = THREE.TWO
SUB = THREE.SUB
ENUMERATE_THREE = THREE.enumerate_three_copy_metatiles


class SqliteMetatileList:
    """Read a canonical metatile alphabet in small ordered chunks."""

    def __init__(self, path: Path, count: int, chunk_size: int = 100):
        self.path = path
        self.count = count
        self.chunk_size = chunk_size
        self.chunk_start = -1
        self.chunk = []
        self.connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)

    def __len__(self):
        return self.count

    def __getitem__(self, index):
        if index < 0:
            index += self.count
        if not 0 <= index < self.count:
            raise IndexError(index)
        start = (index // self.chunk_size) * self.chunk_size
        if start != self.chunk_start:
            rows = self.connection.execute(
                "SELECT r.value_json FROM canonical_order AS o "
                "JOIN representatives AS r USING(sort_key) "
                "WHERE o.canonical_index>=? AND o.canonical_index<? "
                "ORDER BY o.canonical_index",
                (start, min(self.count, start + self.chunk_size)),
            )
            self.chunk = [json.loads(row[0]) for row in rows]
            self.chunk_start = start
        return self.chunk[index - start]


def sqlite_enumeration(record, include_reflections, path: Path):
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        metadata = {
            key: json.loads(value_json)
            for key, value_json in connection.execute("SELECT key,value_json FROM metadata")
        }
    finally:
        connection.close()
    if (metadata.get("id") != record["id"]
            or metadata.get("include_reflections") != include_reflections
            or metadata.get("copies") != 4):
        raise ValueError(f"four-copy SQLite cache identity mismatch: {path}")
    count = metadata["symmetry_distinct_metatiles"]
    return {
        **{key: metadata[key] for key in (
            "raw_connected_extensions", "symmetry_distinct_metatiles",
            "canonical_sha256", "three_copy_parent_total",
            "three_copy_parent_range", "range_receipts")},
        "metatiles": SqliteMetatileList(path, count),
    }


def enumerate_four_copy_metatiles(record, include_reflections=False,
                                  three_parent_start=0, three_parent_stop=0):
    """Enumerate every connected four-copy union modulo the selected A2 group.

    Every connected four-vertex contact graph has a vertex whose removal leaves
    a connected three-vertex graph, so extending the complete three-copy census
    by every legal face-adjacent prototile copy is complete.
    """
    prototile = record["alcoves"]
    orientations = SUB.oriented_cells(prototile, include_reflections)
    three = ENUMERATE_THREE(record, include_reflections)
    representatives = {}
    raw = 0
    start = max(0, three_parent_start)
    stop = min(
        len(three["metatiles"]),
        three_parent_stop if three_parent_stop > 0 else len(three["metatiles"]),
    )
    if start >= stop:
        raise ValueError(f"empty three-copy parent range [{start}, {stop})")
    for three_index in range(start, stop):
        metatile = three["metatiles"][three_index]
        cluster = metatile["alcoves"]
        occupied = {SUB.cell_key(cell) for cell in cluster}
        for neighbor in TWO.adjacent_atomic_cells(cluster):
            neighbor_key = SUB.cell_key(neighbor)
            for orientation_index, orientation in enumerate(orientations):
                for own_cell in orientation["cells"]:
                    own_key = SUB.cell_key(own_cell)
                    if own_key[3] != neighbor_key[3]:
                        continue
                    delta = tuple(neighbor_key[axis] - own_key[axis] for axis in range(3))
                    partner = TWO.translated_cells(orientation["cells"], delta)
                    partner_keys = {SUB.cell_key(cell) for cell in partner}
                    if occupied.intersection(partner_keys):
                        continue
                    raw += 1
                    union = [*cluster, *partner]
                    canonical = TWO.canonical_key(union, include_reflections)
                    if canonical in representatives:
                        continue
                    replay = TWO.replay_base_decomposition(cluster, partner, union)
                    if not replay["verified"]:
                        raise RuntimeError(f"four-copy base replay failed: {replay}")
                    representatives[canonical] = {
                        "alcoves": union,
                        "canonical_key": [list(cell) for cell in canonical],
                        "base_decomposition": {
                            "three_copy_parent_index": three_index,
                            "partner_orientation_index": orientation_index,
                            "partner_translation": list(delta),
                            "replay": replay,
                        },
                    }
    metatiles = [representatives[key] for key in sorted(representatives)]
    digest = hashlib.sha256(json.dumps(
        [item["canonical_key"] for item in metatiles], separators=(",", ":")
    ).encode()).hexdigest()
    return {
        "raw_connected_extensions": raw,
        "symmetry_distinct_metatiles": len(metatiles),
        "canonical_sha256": digest,
        "three_copy_parent_total": len(three["metatiles"]),
        "three_copy_parent_range": [start, stop],
        "metatiles": metatiles,
    }


def cached_enumeration(record, include_reflections, cache_path=None):
    """Load or atomically create a reusable canonical four-copy census."""
    if not cache_path:
        return enumerate_four_copy_metatiles(record, include_reflections)
    path = Path(cache_path)
    if path.exists():
        if path.suffix == ".sqlite":
            return sqlite_enumeration(record, include_reflections, path)
        receipt = json.loads(path.read_text())
        if (receipt.get("id") != record["id"]
                or receipt.get("include_reflections") != include_reflections
                or receipt.get("copies") != 4):
            raise ValueError(f"four-copy enumeration cache identity mismatch: {path}")
        return receipt["enumerated"]
    enumerated = enumerate_four_copy_metatiles(record, include_reflections)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps({
        "id": record["id"],
        "include_reflections": include_reflections,
        "copies": 4,
        "enumerated": enumerated,
    }, separators=(",", ":")))
    os.replace(temporary, path)
    return enumerated


def screen_candidate(record, scale, timeout_ms, include_reflections=False,
                     max_parents=0, defer_exact=False, parent_start=0,
                     parent_stop=0, enumeration_cache=None):
    """Reuse the independently replayed mixed-cover engine with a four-copy census."""
    original = THREE.enumerate_three_copy_metatiles
    THREE.enumerate_three_copy_metatiles = lambda item, reflected=False: cached_enumeration(
        item, reflected, enumeration_cache
    )
    try:
        result = THREE.screen_candidate(
            record, scale, timeout_ms, include_reflections, max_parents,
            defer_exact, parent_start, parent_stop,
        )
    finally:
        THREE.enumerate_three_copy_metatiles = original
    result["classification"] = result["classification"].replace(
        "three_copy", "four_copy"
    )
    detail = result.pop("three_copy_alcove_metatile_screen")
    detail["family"] = "all_face_connected_four_copy_metatiles_modulo_selected_a2_group"
    result["four_copy_alcove_metatile_screen"] = detail
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--max-parents", type=int, default=0)
    parser.add_argument("--parent-start", type=int, default=0)
    parser.add_argument("--parent-stop", type=int, default=0)
    parser.add_argument("--defer-exact", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--enumeration-cache")
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines()
               if line.strip()]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen_candidate(
                record, args.scale, args.timeout_ms, args.include_reflections,
                args.max_parents, args.defer_exact, args.parent_start, args.parent_stop,
                args.enumeration_cache,
            )
            classification = result["classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            detail = result["four_copy_alcove_metatile_screen"]
            print(f"{index}/{len(records)} {record['id']} {classification} "
                  f"({detail['symmetry_distinct_metatiles']} types, "
                  f"{detail['parents_completed']} parents)", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
