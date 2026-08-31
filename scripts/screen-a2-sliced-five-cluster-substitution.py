#!/usr/bin/env python3
"""Exact mixed substitution screen for connected five-copy A2 metatiles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FOUR = load("a2_sliced_four_cluster", "screen-a2-sliced-four-cluster-substitution.py")
THREE = FOUR.THREE
TWO = FOUR.TWO
SUB = FOUR.SUB


def enumerate_five_copy_metatiles(record, cache_path: Path,
                                  include_reflections=False):
    """Extend the complete four-copy cache by every legal adjacent copy.

    Every connected five-vertex contact graph has a vertex whose deletion
    leaves a connected four-vertex graph.  Extending every canonical
    four-copy parent is therefore complete for face-connected metatiles.
    """
    four = FOUR.cached_enumeration(record, include_reflections, cache_path)
    orientations = SUB.oriented_cells(record["alcoves"], include_reflections)
    representatives = {}
    raw = 0
    for four_index, metatile in enumerate(four["metatiles"]):
        cluster = metatile["alcoves"]
        occupied = {SUB.cell_key(cell) for cell in cluster}
        for neighbor in TWO.adjacent_atomic_cells(cluster):
            neighbor_key = SUB.cell_key(neighbor)
            for orientation_index, orientation in enumerate(orientations):
                for own_cell in orientation["cells"]:
                    own_key = SUB.cell_key(own_cell)
                    if own_key[3] != neighbor_key[3]:
                        continue
                    delta = tuple(
                        neighbor_key[axis] - own_key[axis] for axis in range(3)
                    )
                    partner = TWO.translated_cells(orientation["cells"], delta)
                    partner_keys = {SUB.cell_key(cell) for cell in partner}
                    if occupied.intersection(partner_keys):
                        continue
                    raw += 1
                    union = [*cluster, *partner]
                    canonical = TWO.canonical_key(union, include_reflections)
                    if canonical in representatives:
                        continue
                    checked = TWO.replay_base_decomposition(cluster, partner, union)
                    if not checked["verified"]:
                        raise RuntimeError(f"five-copy base replay failed: {checked}")
                    representatives[canonical] = {
                        "alcoves": union,
                        "canonical_key": [list(cell) for cell in canonical],
                        "base_decomposition": {
                            "four_copy_parent_index": four_index,
                            "partner_orientation_index": orientation_index,
                            "partner_translation": list(delta),
                            "replay": checked,
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
        "four_copy_parent_total": len(four["metatiles"]),
        "metatiles": metatiles,
    }


def screen_candidate(record, scale, timeout_ms, cache_path,
                     include_reflections=False, max_parents=0,
                     defer_exact=False, parent_start=0, parent_stop=0):
    enumerated = enumerate_five_copy_metatiles(
        record, Path(cache_path), include_reflections
    )
    original = THREE.enumerate_three_copy_metatiles
    THREE.enumerate_three_copy_metatiles = lambda item, reflected=False: enumerated
    try:
        result = THREE.screen_candidate(
            record, scale, timeout_ms, include_reflections, max_parents,
            defer_exact, parent_start, parent_stop,
        )
    finally:
        THREE.enumerate_three_copy_metatiles = original
    result["classification"] = result["classification"].replace(
        "three_copy", "five_copy"
    )
    detail = result.pop("three_copy_alcove_metatile_screen")
    detail["family"] = (
        "all_face_connected_five_copy_metatiles_modulo_selected_a2_group"
    )
    detail["four_copy_parent_total"] = enumerated["four_copy_parent_total"]
    result["five_copy_alcove_metatile_screen"] = detail
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--enumeration-cache", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--max-parents", type=int, default=0)
    parser.add_argument("--parent-start", type=int, default=0)
    parser.add_argument("--parent-stop", type=int, default=0)
    parser.add_argument("--defer-exact", action="store_true")
    parser.add_argument("--only-unresolved", action="store_true")
    parser.add_argument("--ids", default="")
    args = parser.parse_args()
    records = TWO.read_ndjson(Path(args.input))
    if args.only_unresolved:
        records = [record for record in records
                   if record.get("classification") == "unresolved"]
    requested = {value for value in args.ids.split(",") if value}
    if requested:
        records = [record for record in records if record["id"] in requested]
    if len(records) != 1:
        parser.error("five-copy screen currently requires exactly one candidate")
    result = screen_candidate(
        records[0], args.scale, args.timeout_ms, args.enumeration_cache,
        args.include_reflections, args.max_parents, args.defer_exact,
        args.parent_start, args.parent_stop,
    )
    Path(args.output).write_text(json.dumps(result, separators=(",", ":")) + "\n")
    detail = result["five_copy_alcove_metatile_screen"]
    print(json.dumps({
        "id": result["id"],
        "classification": result["classification"],
        "four_copy_parents": detail["four_copy_parent_total"],
        "five_copy_metatiles": detail["symmetry_distinct_metatiles"],
        "parents_completed": detail["parents_completed"],
        "parent_counts": detail["parent_counts"],
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
