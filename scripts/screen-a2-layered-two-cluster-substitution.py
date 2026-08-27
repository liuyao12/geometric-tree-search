#!/usr/bin/env python3
"""Exact scalar self-substitution screen for two-copy A2 metatiles.

For each monotile, enumerate every face-connected union of two legal copies,
modulo translation and the proper symmetry group of the A2-layer lattice.
Each union is then treated as a metatile and its scalar inflation is tested
for an exact cover by congruent copies of that same metatile.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUBSTITUTION = load("a2_substitution", "screen-a2-layered-substitution.py")
GEOMETRY = SUBSTITUTION.GEOMETRY


def cell_faces(cell):
    vertices = GEOMETRY.cell_vertices(cell)
    return {
        tuple(sorted((vertices[0], vertices[1], vertices[2]))),
        tuple(sorted((vertices[3], vertices[4], vertices[5]))),
        tuple(sorted((vertices[0], vertices[1], vertices[4], vertices[3]))),
        tuple(sorted((vertices[1], vertices[2], vertices[5], vertices[4]))),
        tuple(sorted((vertices[2], vertices[0], vertices[3], vertices[5]))),
    }


def translated_cells(cells, delta):
    return [
        {
            "q": cell["q"] + delta[0],
            "r": cell["r"] + delta[1],
            "k": cell["k"] + delta[2],
            "kind": cell["kind"],
        }
        for cell in cells
    ]


def normalized_key(cells):
    keys = [SUBSTITUTION.cell_key(cell) for cell in cells]
    min_q = min(key[0] for key in keys)
    min_r = min(key[1] for key in keys)
    min_k = min(key[2] for key in keys)
    return tuple(sorted(
        (q - min_q, r - min_r, k - min_k, kind)
        for q, r, k, kind in keys
    ))


def canonical_key(cells):
    return min(
        normalized_key(orientation["cells"])
        for orientation in SUBSTITUTION.oriented_cells(cells)
    )


def adjacent_atomic_cells(root_cells):
    root_keys = {SUBSTITUTION.cell_key(cell) for cell in root_cells}
    neighbors = {}
    for root in root_cells:
        q, r, k, kind = SUBSTITUTION.cell_key(root)
        if kind == "u":
            candidates = (
                (q, r, k - 1, "u"), (q, r, k + 1, "u"),
                (q, r, k, "d"), (q - 1, r, k, "d"),
                (q, r - 1, k, "d"),
            )
        else:
            candidates = (
                (q, r, k - 1, "d"), (q, r, k + 1, "d"),
                (q, r, k, "u"), (q + 1, r, k, "u"),
                (q, r + 1, k, "u"),
            )
        for key in candidates:
            if key in root_keys or key in neighbors:
                continue
            cell = {"q": key[0], "r": key[1], "k": key[2], "kind": key[3]}
            if len(cell_faces(root).intersection(cell_faces(cell))) != 1:
                raise RuntimeError("A2 atomic neighbor table failed full-face replay")
            neighbors[key] = cell
    return list(neighbors.values())


def replay_base_decomposition(root_cells, partner_cells, union_cells):
    root = {SUBSTITUTION.cell_key(cell) for cell in root_cells}
    partner = {SUBSTITUTION.cell_key(cell) for cell in partner_cells}
    union = {SUBSTITUTION.cell_key(cell) for cell in union_cells}
    # Rebuild faces from dictionaries; the deliberately separate replay does
    # not trust the enumeration's neighbor anchor.
    root_face_keys = set().union(*(cell_faces(cell) for cell in root_cells))
    partner_face_keys = set().union(*(cell_faces(cell) for cell in partner_cells))
    verified = not root.intersection(partner) and root.union(partner) == union
    verified = verified and bool(root_face_keys.intersection(partner_face_keys))
    return {
        "verified": verified,
        "method": "independent_atomic_cells_and_shared_face_replay",
        "root_cells": len(root),
        "partner_cells": len(partner),
        "shared_full_faces": len(root_face_keys.intersection(partner_face_keys)),
    }


def enumerate_two_copy_metatiles(record):
    root_cells = record["cells"]
    root_keys = {SUBSTITUTION.cell_key(cell) for cell in root_cells}
    orientations = SUBSTITUTION.oriented_cells(root_cells)
    neighbors = adjacent_atomic_cells(root_cells)
    representatives = {}
    raw_placements = 0
    for orientation_index, orientation in enumerate(orientations):
        for neighbor in neighbors:
            neighbor_key = SUBSTITUTION.cell_key(neighbor)
            for own_cell in orientation["cells"]:
                own_key = SUBSTITUTION.cell_key(own_cell)
                if own_key[3] != neighbor_key[3]:
                    continue
                delta = tuple(neighbor_key[axis] - own_key[axis] for axis in range(3))
                partner = translated_cells(orientation["cells"], delta)
                partner_keys = {SUBSTITUTION.cell_key(cell) for cell in partner}
                if root_keys.intersection(partner_keys):
                    continue
                raw_placements += 1
                union = [*root_cells, *partner]
                key = canonical_key(union)
                if key in representatives:
                    continue
                replay = replay_base_decomposition(root_cells, partner, union)
                if not replay["verified"]:
                    raise RuntimeError(f"base metatile replay failed: {replay}")
                representatives[key] = {
                    "cells": union,
                    "canonical_key": [list(cell) for cell in key],
                    "base_decomposition": {
                        "root_orientation_index": 0,
                        "partner_orientation_index": orientation_index,
                        "partner_translation": list(delta),
                        "replay": replay,
                    },
                }
    ordered = [representatives[key] for key in sorted(representatives)]
    digest = hashlib.sha256(json.dumps(
        [item["canonical_key"] for item in ordered], separators=(",", ":")
    ).encode()).hexdigest()
    return {
        "raw_face_connected_placements": raw_placements,
        "symmetry_distinct_metatiles": len(ordered),
        "canonical_sha256": digest,
        "metatiles": ordered,
    }


def oriented_metatile_alphabet(metatiles):
    alphabet = []
    for type_index, metatile in enumerate(metatiles):
        for orientation_index, orientation in enumerate(
            SUBSTITUTION.oriented_cells(metatile["cells"])
        ):
            alphabet.append({
                "type_index": type_index,
                "orientation_index": orientation_index,
                "cells": [SUBSTITUTION.cell_key(cell) for cell in orientation["cells"]],
            })
    return alphabet


def first_mixed_uncovered_cell(target, alphabet):
    for target_cell in sorted(target):
        covered = False
        for orientation in alphabet:
            for own_cell in orientation["cells"]:
                if own_cell[3] != target_cell[3]:
                    continue
                delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
                if all(
                    (
                        cell[0] + delta[0], cell[1] + delta[1],
                        cell[2] + delta[2], cell[3],
                    ) in target
                    for cell in orientation["cells"]
                ):
                    covered = True
                    break
            if covered:
                break
        if not covered:
            return target_cell
    return None


def replay_mixed_local_obstruction(target, metatiles, target_cell):
    placements_checked = 0
    for type_index, metatile in enumerate(metatiles):
        for orientation_index, orientation in enumerate(
            SUBSTITUTION.oriented_cells(metatile["cells"])
        ):
            own = [SUBSTITUTION.cell_key(cell) for cell in orientation["cells"]]
            for own_cell in own:
                if own_cell[3] != target_cell[3]:
                    continue
                placements_checked += 1
                delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
                translated = {
                    (
                        cell[0] + delta[0], cell[1] + delta[1],
                        cell[2] + delta[2], cell[3],
                    )
                    for cell in own
                }
                if translated.issubset(target):
                    return {
                        "verified": False,
                        "reason": "covering_metatile_placement_exists",
                        "type_index": type_index,
                        "orientation_index": orientation_index,
                        "placements_checked": placements_checked,
                    }
    return {
        "verified": True,
        "method": "independent_all_metatile_types_orientations_and_anchors",
        "uncovered_cell": list(target_cell),
        "placements_checked": placements_checked,
    }


def mixed_candidate_placements(target, metatiles):
    placements = []
    for type_index, metatile in enumerate(metatiles):
        orientations = SUBSTITUTION.oriented_cells(metatile["cells"])
        for placement in SUBSTITUTION.candidate_placements(target, orientations):
            placements.append({**placement, "type_index": type_index})
    return placements


def screen_mixed_alphabet(metatiles, scale, timeout_ms):
    alphabet = oriented_metatile_alphabet(metatiles)
    parent_results = []
    for parent_index, parent in enumerate(metatiles):
        target = SUBSTITUTION.scaled_cells(parent["cells"], scale)
        uncovered = first_mixed_uncovered_cell(target, alphabet)
        if uncovered is not None:
            replay = replay_mixed_local_obstruction(target, metatiles, uncovered)
            if not replay["verified"]:
                raise RuntimeError(f"mixed local obstruction replay failed: {replay}")
            parent_results.append({
                "parent_index": parent_index,
                "classification": "local_obstruction",
                "target_cells": len(target),
                "local_obstruction_replay": replay,
            })
            continue

        placements = mixed_candidate_placements(target, metatiles)
        solved = SUBSTITUTION.exact_cover(target, placements, timeout_ms)
        common = {
            "parent_index": parent_index,
            "target_cells": len(target),
            "placements_considered": len(placements),
            "nodes": solved["nodes"],
            "failed_states": solved["failed_states"],
        }
        if solved["result"] == "sat":
            replay = SUBSTITUTION.replay(target, placements, solved["solution"], scale ** 3)
            if not replay["verified"]:
                raise RuntimeError(f"mixed substitution replay failed: {replay}")
            parent_results.append({
                **common,
                "classification": "mixed_metatile_rule",
                "rule": [
                    {
                        "type_index": placements[index]["type_index"],
                        "orientation_index": placements[index]["orientation_index"],
                        "translation": placements[index]["translation"],
                    }
                    for index in solved["solution"]
                ],
                "replay": replay,
            })
        elif solved["result"] == "unsat":
            replay = SUBSTITUTION.replay_unsat_with_z3(target, placements, timeout_ms)
            if not replay["verified"]:
                raise RuntimeError(f"mixed substitution UNSAT replay failed: {replay}")
            parent_results.append({
                **common,
                "classification": "exact_unsat",
                "exact_unsat_replay": replay,
            })
        else:
            parent_results.append({
                **common,
                "classification": "unresolved",
                "stopped_by": "time_limit",
            })

    rules = {
        result["parent_index"]: result
        for result in parent_results
        if result["classification"] == "mixed_metatile_rule"
    }
    closed_alphabet = None
    for seed in sorted(rules):
        closure = {seed}
        frontier = [seed]
        valid = True
        while frontier and valid:
            parent_index = frontier.pop()
            rule = rules.get(parent_index)
            if rule is None:
                valid = False
                break
            for child in rule["rule"]:
                child_index = child["type_index"]
                if child_index not in closure:
                    closure.add(child_index)
                    frontier.append(child_index)
        if valid and (closed_alphabet is None or len(closure) < len(closed_alphabet)):
            closed_alphabet = sorted(closure)

    unknowns = [
        result["parent_index"] for result in parent_results
        if result["classification"] == "unresolved"
    ]
    if closed_alphabet is not None:
        classification = "mixed_two_copy_metatile_substitution_system"
        certified = True
    elif not rules and not unknowns:
        classification = f"no_mixed_two_copy_metatile_scalar{scale}_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    return {
        "classification": classification,
        "certified": certified,
        "inflation": f"scalar_{scale}",
        "scale": scale,
        "alphabet": "all_symmetry_distinct_face_connected_two_copy_metatiles",
        "metatile_types": len(metatiles),
        "oriented_metatile_types": len(alphabet),
        "closed_alphabet": closed_alphabet,
        "parent_counts": {
            name: sum(result["classification"] == name for result in parent_results)
            for name in ("local_obstruction", "exact_unsat", "mixed_metatile_rule", "unresolved")
        },
        "parent_results": parent_results,
    }


def screen_candidate(record, timeout_ms, scale=2):
    enumerated = enumerate_two_copy_metatiles(record)
    results = []
    counts = {}
    for index, metatile in enumerate(enumerated["metatiles"]):
        result = SUBSTITUTION.screen({
            "id": f"{record['id']}_two_cluster_{index:04d}",
            "cells": metatile["cells"],
        }, scale, timeout_ms)
        classification = result["substitution_classification"]
        counts[classification] = counts.get(classification, 0) + 1
        results.append({
            "metatile_index": index,
            "cells": metatile["cells"],
            "base_decomposition": metatile["base_decomposition"],
            "classification": classification,
            "substitution": result["substitution"],
        })
    positives = [
        result for result in results
        if result["classification"] == "scalar_substitution_rule"
    ]
    unknowns = [
        result for result in results
        if result["classification"] == "unresolved"
    ]
    classification = (
        "two_copy_metatile_substitution_rule" if positives
        else ("unresolved" if unknowns else f"no_two_copy_metatile_scalar{scale}_substitution")
    )
    mixed = screen_mixed_alphabet(enumerated["metatiles"], scale, timeout_ms)
    if mixed["classification"] == "mixed_two_copy_metatile_substitution_system":
        classification = "two_copy_metatile_substitution_system"
    elif mixed["classification"] == "unresolved":
        classification = "unresolved"
    return {
        "id": record["id"],
        "cells": record["cells"],
        "classification": classification,
        "two_copy_metatile_screen": {
            "certified": not unknowns,
            "inflation": f"scalar_{scale}",
            "scale": scale,
            "family": "all_face_connected_two_copy_metatiles_modulo_proper_a2_isometry_and_translation",
            "raw_face_connected_placements": enumerated["raw_face_connected_placements"],
            "symmetry_distinct_metatiles": enumerated["symmetry_distinct_metatiles"],
            "canonical_sha256": enumerated["canonical_sha256"],
            "counts": counts,
            "positive_metatile_indices": [item["metatile_index"] for item in positives],
            "unknown_metatile_indices": [item["metatile_index"] for item in unknowns],
            "results": results,
        },
        "mixed_two_copy_metatile_screen": mixed,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [
        json.loads(line) for line in Path(args.input).read_text().splitlines()
        if line.strip()
    ]
    if requested:
        records = [record for record in records if record["id"] in requested]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            screened = screen_candidate(record, args.timeout_ms, args.scale)
            classification = screened["classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(screened, separators=(",", ":")) + "\n")
            stream.flush()
            detail = screened["two_copy_metatile_screen"]
            print(
                f"{index}/{len(records)} {record['id']} {classification} "
                f"({detail['symmetry_distinct_metatiles']} metatiles)",
                flush=True,
            )
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
