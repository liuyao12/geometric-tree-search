#!/usr/bin/env python3
"""Exact mixed substitution screen for face-connected two-copy alcove metatiles."""

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


SUB = load("a2_sliced_substitution", "screen-a2-sliced-alcove-substitution.py")


def translated_cells(cells, delta):
    return [{
        "base": [cell["base"][axis] + delta[axis] for axis in range(3)],
        "order": list(cell["order"]),
    } for cell in cells]


def normalized_key(cells):
    keys = [SUB.cell_key(cell) for cell in cells]
    minima = [min(key[axis] for key in keys) for axis in range(3)]
    return tuple(sorted((
        key[0] - minima[0], key[1] - minima[1], key[2] - minima[2], key[3]
    ) for key in keys))


def canonical_key(cells, include_reflections=False):
    return min(normalized_key(orientation["cells"])
               for orientation in SUB.oriented_cells(cells, include_reflections))


def atomic_neighbors(cell):
    base = cell["base"]
    a, b, c = cell["order"]
    shifted_a = [base[axis] + (1 if axis == a else 0) for axis in range(3)]
    shifted_c = [base[axis] - (1 if axis == c else 0) for axis in range(3)]
    return [
        {"base": shifted_a, "order": [b, c, a]},
        {"base": shifted_c, "order": [c, a, b]},
        {"base": list(base), "order": [b, a, c]},
        {"base": list(base), "order": [a, c, b]},
    ]


def cell_faces(cell):
    vertices = SUB.cell_vertices(cell)
    return {tuple(sorted(vertices[index] for index in range(4) if index != omitted))
            for omitted in range(4)}


def adjacent_atomic_cells(root_cells):
    occupied = {SUB.cell_key(cell) for cell in root_cells}
    neighbors = {}
    for root in root_cells:
        for neighbor in atomic_neighbors(root):
            key = SUB.cell_key(neighbor)
            if key in occupied or key in neighbors:
                continue
            if len(cell_faces(root).intersection(cell_faces(neighbor))) != 1:
                raise RuntimeError("alcove neighbor failed full-face replay")
            neighbors[key] = neighbor
    return list(neighbors.values())


def replay_base_decomposition(root_cells, partner_cells, union_cells):
    root = {SUB.cell_key(cell) for cell in root_cells}
    partner = {SUB.cell_key(cell) for cell in partner_cells}
    union = {SUB.cell_key(cell) for cell in union_cells}
    root_faces = set().union(*(cell_faces(cell) for cell in root_cells))
    partner_faces = set().union(*(cell_faces(cell) for cell in partner_cells))
    shared = root_faces.intersection(partner_faces)
    return {
        "verified": not root.intersection(partner) and root.union(partner) == union and bool(shared),
        "method": "independent_alcove_cells_and_shared_face_replay",
        "root_alcoves": len(root),
        "partner_alcoves": len(partner),
        "shared_full_faces": len(shared),
    }


def enumerate_two_copy_metatiles(record, include_reflections=False):
    root_cells = record["alcoves"]
    root_keys = {SUB.cell_key(cell) for cell in root_cells}
    orientations = SUB.oriented_cells(root_cells, include_reflections)
    neighbors = adjacent_atomic_cells(root_cells)
    representatives = {}
    raw = 0
    for orientation_index, orientation in enumerate(orientations):
        for neighbor in neighbors:
            neighbor_key = SUB.cell_key(neighbor)
            for own_cell in orientation["cells"]:
                own_key = SUB.cell_key(own_cell)
                if own_key[3] != neighbor_key[3]:
                    continue
                delta = tuple(neighbor_key[axis] - own_key[axis] for axis in range(3))
                partner = translated_cells(orientation["cells"], delta)
                partner_keys = {SUB.cell_key(cell) for cell in partner}
                if root_keys.intersection(partner_keys):
                    continue
                raw += 1
                union = [*root_cells, *partner]
                key = canonical_key(union, include_reflections)
                if key in representatives:
                    continue
                replay = replay_base_decomposition(root_cells, partner, union)
                if not replay["verified"]:
                    raise RuntimeError(f"two-copy base replay failed: {replay}")
                representatives[key] = {
                    "alcoves": union,
                    "canonical_key": [list(cell) for cell in key],
                    "base_decomposition": {
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
        "raw_face_connected_placements": raw,
        "symmetry_distinct_metatiles": len(metatiles),
        "canonical_sha256": digest,
        "metatiles": metatiles,
    }


def oriented_alphabet(metatiles, include_reflections=False):
    alphabet = []
    for type_index, metatile in enumerate(metatiles):
        for orientation_index, orientation in enumerate(
                SUB.oriented_cells(metatile["alcoves"], include_reflections)):
            alphabet.append({
                "type_index": type_index,
                "orientation_index": orientation_index,
                "cells": [SUB.cell_key(cell) for cell in orientation["cells"]],
            })
    return alphabet


def first_uncovered(target, alphabet):
    for target_cell in sorted(target):
        covered = False
        for orientation in alphabet:
            for own_cell in orientation["cells"]:
                if own_cell[3] != target_cell[3]:
                    continue
                delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
                if all((cell[0] + delta[0], cell[1] + delta[1],
                        cell[2] + delta[2], cell[3]) in target
                       for cell in orientation["cells"]):
                    covered = True
                    break
            if covered:
                break
        if not covered:
            return target_cell
    return None


def replay_local_obstruction(target, alphabet, target_cell):
    checked = 0
    for orientation in alphabet:
        for own_cell in orientation["cells"]:
            if own_cell[3] != target_cell[3]:
                continue
            checked += 1
            delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
            translated = {(cell[0] + delta[0], cell[1] + delta[1],
                           cell[2] + delta[2], cell[3]) for cell in orientation["cells"]}
            if translated.issubset(target):
                return {"verified": False, "reason": "covering_placement_exists"}
    return {
        "verified": True,
        "method": "independent_all_metatile_orientations_and_anchors",
        "uncovered_alcove": list(target_cell),
        "placements_checked": checked,
    }


def mixed_placements(target, alphabet):
    placements = {}
    for orientation in alphabet:
        own = orientation["cells"]
        for target_cell in target:
            for own_cell in own:
                if own_cell[3] != target_cell[3]:
                    continue
                delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
                translated = frozenset((cell[0] + delta[0], cell[1] + delta[1],
                                        cell[2] + delta[2], cell[3]) for cell in own)
                key = (orientation["type_index"], translated)
                if translated.issubset(target) and key not in placements:
                    placements[key] = {
                        "type_index": orientation["type_index"],
                        "orientation_index": orientation["orientation_index"],
                        "translation": list(delta),
                        "cells": translated,
                    }
    return list(placements.values())


def screen_candidate(record, scale, timeout_ms, include_reflections=False,
                     max_parents=0):
    enumerated = enumerate_two_copy_metatiles(record, include_reflections)
    metatiles = enumerated["metatiles"]
    alphabet = oriented_alphabet(metatiles, include_reflections)
    limit = min(len(metatiles), max_parents) if max_parents > 0 else len(metatiles)
    results = []
    for parent_index, parent in enumerate(metatiles[:limit]):
        target = SUB.inflated_cells(parent["alcoves"], scale)
        uncovered = first_uncovered(target, alphabet)
        if uncovered is not None:
            replay = replay_local_obstruction(target, alphabet, uncovered)
            if not replay["verified"]:
                raise RuntimeError(f"local obstruction replay failed: {replay}")
            results.append({
                "parent_index": parent_index,
                "classification": "local_obstruction",
                "target_alcoves": len(target),
                "local_obstruction_replay": replay,
            })
            continue
        placements = mixed_placements(target, alphabet)
        solved = SUB.exact_cover(target, placements, timeout_ms)
        common = {
            "parent_index": parent_index,
            "target_alcoves": len(target),
            "placements_considered": len(placements),
            "nodes": solved["nodes"],
            "failed_states": solved["failed_states"],
        }
        if solved["result"] == "sat":
            replay = SUB.replay(target, placements, solved["solution"], scale ** 3)
            if not replay["verified"]:
                raise RuntimeError(f"mixed rule replay failed: {replay}")
            results.append({
                **common,
                "classification": "mixed_metatile_rule",
                "rule": [{
                    "type_index": placements[index]["type_index"],
                    "orientation_index": placements[index]["orientation_index"],
                    "translation": placements[index]["translation"],
                } for index in solved["solution"]],
                "replay": replay,
            })
        elif solved["result"] == "unsat":
            replay = SUB.replay_unsat_with_z3(target, placements, timeout_ms)
            if not replay["verified"]:
                raise RuntimeError(f"mixed UNSAT replay failed: {replay}")
            results.append({**common, "classification": "exact_unsat",
                            "exact_unsat_replay": replay})
        else:
            results.append({**common, "classification": "unresolved",
                            "stopped_by": "time_limit"})

    rules = {result["parent_index"]: result for result in results
             if result["classification"] == "mixed_metatile_rule"}
    closed = None
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
                if child["type_index"] not in closure:
                    closure.add(child["type_index"])
                    frontier.append(child["type_index"])
        if valid and (closed is None or len(closure) < len(closed)):
            closed = sorted(closure)
    complete = limit == len(metatiles)
    unknowns = [result for result in results if result["classification"] == "unresolved"]
    if closed is not None:
        classification = "two_copy_metatile_substitution_system"
        certified = True
    elif complete and not rules and not unknowns:
        classification = f"no_two_copy_metatile_scalar{scale}_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    return {
        "id": record["id"],
        "classification": classification,
        "two_copy_alcove_metatile_screen": {
            "certified": certified,
            "scale": scale,
            "include_reflections": include_reflections,
            "family": "all_face_connected_two_copy_metatiles_modulo_selected_a2_group",
            **{key: enumerated[key] for key in (
                "raw_face_connected_placements", "symmetry_distinct_metatiles",
                "canonical_sha256")},
            "oriented_metatile_types": len(alphabet),
            "parents_completed": len(results),
            "closed_alphabet": closed,
            "parent_counts": {kind: sum(result["classification"] == kind for result in results)
                              for kind in ("local_obstruction", "exact_unsat",
                                           "mixed_metatile_rule", "unresolved")},
            "parent_results": results,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--max-parents", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
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
            result = screen_candidate(record, args.scale, args.timeout_ms,
                                      args.include_reflections, args.max_parents)
            counts[result["classification"]] = counts.get(result["classification"], 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            detail = result["two_copy_alcove_metatile_screen"]
            print(f"{index}/{len(records)} {record['id']} {result['classification']} "
                  f"({detail['symmetry_distinct_metatiles']} types, "
                  f"{detail['parents_completed']} parents)", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
