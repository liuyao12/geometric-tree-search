#!/usr/bin/env python3
"""Resumable exact enumeration of connected four-copy A2 metatiles."""

from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.util
import json
import sqlite3
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


THREE = load("a2_three_cluster", "screen-a2-layered-three-cluster-substitution.py")
TWO = THREE.TWO
SUBSTITUTION = THREE.SUBSTITUTION
GEOMETRY = SUBSTITUTION.GEOMETRY
ISOMETRIES = tuple(
    (sign, tuple(permutation))
    for sign, permutation in GEOMETRY.A2_LAYER_ISOMETRIES
)
KIND_TO_INT = {"d": 0, "u": 1}
INT_TO_KIND = ("d", "u")


@functools.lru_cache(maxsize=None)
def transformed_cell(sign, permutation, q, r, k, kind):
    vertices = [
        tuple(sign * point[permutation[axis]] for axis in range(3))
        for point in GEOMETRY.cell_vertices({"q": q, "r": r, "k": k, "kind": kind})
    ]
    return SUBSTITUTION.cell_key(SUBSTITUTION.cell_from_vertices(vertices))


def packed_canonical_key(cells):
    """Canonicalize exactly as TWO.canonical_key, with cached cell actions."""
    keys = [SUBSTITUTION.cell_key(cell) if isinstance(cell, dict) else cell for cell in cells]
    candidates = []
    for sign, permutation in ISOMETRIES:
        transformed = [
            transformed_cell(sign, permutation, q, r, k, kind)
            for q, r, k, kind in keys
        ]
        min_q = min(cell[0] for cell in transformed)
        min_r = min(cell[1] for cell in transformed)
        min_k = min(cell[2] for cell in transformed)
        encoded = sorted(
            ((q - min_q) << 24)
            | ((r - min_r) << 16)
            | ((k - min_k) << 8)
            | KIND_TO_INT[kind]
            for q, r, k, kind in transformed
        )
        if encoded[-1] >= 1 << 32:
            raise RuntimeError("four-copy canonical coordinate exceeds packed key")
        candidates.append(b"".join(value.to_bytes(4, "big") for value in encoded))
    return min(candidates)


def unpack_key(packed):
    cells = []
    for offset in range(0, len(packed), 4):
        value = int.from_bytes(packed[offset:offset + 4], "big")
        cells.append((
            (value >> 24) & 255,
            (value >> 16) & 255,
            (value >> 8) & 255,
            INT_TO_KIND[value & 255],
        ))
    return tuple(cells)


def cells_as_dicts(cells):
    return [
        {"q": q, "r": r, "k": k, "kind": kind}
        for q, r, k, kind in cells
    ]


def attachment_placements(cluster_cells, orientation_keys):
    occupied = set(cluster_cells)
    boundary = TWO.adjacent_atomic_cells(cells_as_dicts(cluster_cells))
    placements = set()
    for neighbor in boundary:
        neighbor_key = SUBSTITUTION.cell_key(neighbor)
        for orientation in orientation_keys:
            for own_cell in orientation:
                if own_cell[3] != neighbor_key[3]:
                    continue
                delta = tuple(neighbor_key[axis] - own_cell[axis] for axis in range(3))
                placed = frozenset(
                    (
                        q + delta[0], r + delta[1], k + delta[2], kind,
                    )
                    for q, r, k, kind in orientation
                )
                if occupied.isdisjoint(placed):
                    placements.add(placed)
    return placements


def extend_in_memory(base_keys, orientation_keys):
    representatives = set()
    raw_placements = 0
    for packed in base_keys:
        cluster = unpack_key(packed)
        placements = attachment_placements(cluster, orientation_keys)
        raw_placements += len(placements)
        for placement in placements:
            representatives.add(packed_canonical_key((*cluster, *placement)))
    return sorted(representatives), raw_placements


def family_sha256(packed_keys):
    digest = hashlib.sha256()
    digest.update(b"[")
    for index, packed in enumerate(packed_keys):
        if index:
            digest.update(b",")
        digest.update(json.dumps(
            [list(cell) for cell in unpack_key(packed)],
            separators=(",", ":"),
        ).encode())
    digest.update(b"]")
    return digest.hexdigest()


def source_sha256(record):
    return hashlib.sha256(json.dumps(
        sorted(SUBSTITUTION.cell_key(cell) for cell in record["cells"]),
        separators=(",", ":"),
    ).encode()).hexdigest()


def published_three_copy_receipt(record):
    path = ROOT / "data" / (
        f"a2-layered-size7-three-cluster-substitution-scalar2-{record['id']}.ndjson"
    )
    if path.exists():
        report = json.loads(path.read_text())
        screen = report["three_copy_metatile_screen"]
        return screen["symmetry_distinct_metatiles"], screen["canonical_sha256"]

    compact = ROOT / "data" / "a2-layered-size8-substitution-screen-summary.ndjson"
    if compact.exists():
        for line in compact.read_text().splitlines():
            report = json.loads(line)
            screen = report.get("three_copy_metatile_screen")
            if (
                report.get("id") == record["id"]
                and screen is not None
                and screen.get("scale") == 2
                and screen.get("certified") is True
            ):
                return screen["symmetry_distinct_metatiles"], screen["canonical_sha256"]

    enumerated = THREE.enumerate_three_copy_metatiles(record)
    return enumerated["symmetry_distinct_metatiles"], enumerated["canonical_sha256"]


def open_checkpoint(path, record, three_keys, three_hash):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS four_keys (key BLOB PRIMARY KEY)")
    expected = {
        "candidate_id": record["id"],
        "source_sha256": source_sha256(record),
        "three_copy_types": str(len(three_keys)),
        "three_copy_sha256": three_hash,
        "enumeration_model": "connected_extension_modulo_proper_a2_isometry_and_translation_v1",
    }
    existing = dict(connection.execute("SELECT name, value FROM meta"))
    if existing:
        for name, value in expected.items():
            if existing.get(name) != value:
                raise RuntimeError(f"enumeration checkpoint mismatch for {name}")
    else:
        connection.executemany("INSERT INTO meta(name, value) VALUES (?, ?)", expected.items())
        connection.execute("INSERT INTO meta(name, value) VALUES ('bases_completed', '0')")
        connection.execute("INSERT INTO meta(name, value) VALUES ('raw_attachment_placements', '0')")
        connection.commit()
    return connection


def enumerate_four_copy(record, checkpoint, checkpoint_every=25, progress_every=100):
    orientations = SUBSTITUTION.oriented_cells(record["cells"])
    orientation_keys = [
        tuple(SUBSTITUTION.cell_key(cell) for cell in orientation["cells"])
        for orientation in orientations
    ]
    two = TWO.enumerate_two_copy_metatiles(record)
    two_keys = sorted(packed_canonical_key(item["cells"]) for item in two["metatiles"])
    three_keys, three_raw = extend_in_memory(two_keys, orientation_keys)
    three_hash = family_sha256(three_keys)
    connection = open_checkpoint(checkpoint, record, three_keys, three_hash)
    meta = dict(connection.execute("SELECT name, value FROM meta"))
    completed = int(meta["bases_completed"])
    raw_placements = int(meta["raw_attachment_placements"])
    if completed > len(three_keys):
        raise RuntimeError("enumeration checkpoint exceeds three-copy alphabet")
    started = time.monotonic()
    transaction_open = False
    for base_index in range(completed, len(three_keys)):
        if not transaction_open:
            connection.execute("BEGIN IMMEDIATE")
            transaction_open = True
        cluster = unpack_key(three_keys[base_index])
        placements = attachment_placements(cluster, orientation_keys)
        raw_placements += len(placements)
        connection.executemany(
            "INSERT OR IGNORE INTO four_keys(key) VALUES (?)",
            ((packed_canonical_key((*cluster, *placement)),) for placement in placements),
        )
        completed = base_index + 1
        if completed % checkpoint_every == 0 or completed == len(three_keys):
            connection.execute(
                "UPDATE meta SET value = ? WHERE name = 'bases_completed'", (str(completed),)
            )
            connection.execute(
                "UPDATE meta SET value = ? WHERE name = 'raw_attachment_placements'",
                (str(raw_placements),),
            )
            connection.commit()
            transaction_open = False
        if progress_every and completed % progress_every == 0:
            count = connection.execute("SELECT COUNT(*) FROM four_keys").fetchone()[0]
            print(
                f"{record['id']} bases {completed}/{len(three_keys)} "
                f"four_types {count} elapsed_s {round(time.monotonic() - started, 1)}",
                flush=True,
            )
    four_count = connection.execute("SELECT COUNT(*) FROM four_keys").fetchone()[0]
    four_hash = family_sha256(
        row[0] for row in connection.execute("SELECT key FROM four_keys ORDER BY key")
    )
    connection.execute(
        "INSERT OR REPLACE INTO meta(name, value) VALUES ('four_copy_types', ?)",
        (str(four_count),),
    )
    connection.execute(
        "INSERT OR REPLACE INTO meta(name, value) VALUES ('four_copy_sha256', ?)",
        (four_hash,),
    )
    connection.commit()
    expected_three_count, expected_three_hash = published_three_copy_receipt(record)
    result = {
        "id": record["id"],
        "cells": record["cells"],
        "four_copy_metatile_enumeration": {
            "certified": True,
            "family": "all_face_connected_four_copy_metatiles_modulo_proper_a2_isometry_and_translation",
            "construction": "extend_complete_three_copy_family_by_every_disjoint_face_adjacent_monotile_placement",
            "two_copy_types": len(two_keys),
            "three_copy_types": len(three_keys),
            "three_copy_raw_attachment_placements": three_raw,
            "three_copy_sha256": three_hash,
            "three_copy_expected_types": expected_three_count,
            "three_copy_expected_sha256": expected_three_hash,
            "three_copy_hash_verified": None,
            "raw_fourth_copy_placements": raw_placements,
            "symmetry_distinct_metatiles": four_count,
            "canonical_sha256": four_hash,
            "transform_cache": {
                "hits": transformed_cell.cache_info().hits,
                "misses": transformed_cell.cache_info().misses,
            },
        },
    }
    result["four_copy_metatile_enumeration"]["three_copy_hash_verified"] = (
        len(three_keys) == expected_three_count
        and result["four_copy_metatile_enumeration"]["three_copy_sha256"]
        == result["four_copy_metatile_enumeration"]["three_copy_expected_sha256"]
    )
    if not result["four_copy_metatile_enumeration"]["three_copy_hash_verified"]:
        raise RuntimeError("optimized three-copy enumeration disagrees with published enumerator")
    connection.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--checkpoint-every", type=int, default=25)
    parser.add_argument("--progress-every", type=int, default=100)
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    record = next(record for record in records if record["id"] == args.id)
    result = enumerate_four_copy(
        record, Path(args.checkpoint), args.checkpoint_every, args.progress_every
    )
    Path(args.output).write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps(result["four_copy_metatile_enumeration"], indent=2))


if __name__ == "__main__":
    main()
