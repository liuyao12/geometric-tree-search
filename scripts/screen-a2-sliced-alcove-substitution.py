#!/usr/bin/env python3
"""Exact scalar substitution screen for A2-sliced Coxeter-alcove unions."""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
COVER = load("a2_substitution_cover", "screen-a2-layered-substitution.py")
PERMUTATIONS = tuple(itertools.permutations(range(3)))


def cell_key(cell: dict) -> tuple[int, int, int, str]:
    return (*cell["base"], "".join(map(str, cell["order"])))


def cell_vertices(cell: dict) -> list[tuple[int, int, int]]:
    base = tuple(cell["base"])
    order = cell["order"]
    points = [base]
    current = list(base)
    for axis in order:
        current = current.copy()
        current[axis] += 1
        points.append(tuple(current))
    return points


def cell_from_vertices(vertices) -> dict:
    base = tuple(min(point[axis] for point in vertices) for axis in range(3))
    ranked = sorted(vertices, key=lambda point: sum(
        point[axis] - base[axis] for axis in range(3)
    ))
    ranks = [sum(point[axis] - base[axis] for axis in range(3)) for point in ranked]
    if ranks != [0, 1, 2, 3]:
        raise ValueError("transformed simplex left the Coxeter-alcove complex")
    order = []
    for previous, current in zip(ranked, ranked[1:]):
        changed = [axis for axis in range(3) if current[axis] - previous[axis] == 1]
        if len(changed) != 1:
            raise ValueError("could not recover transformed alcove order")
        order.append(changed[0])
    return {"base": list(base), "order": order}


def oriented_cells(cells: list[dict], include_reflections: bool = False) -> list[dict]:
    result = []
    seen = set()
    isometries = (
        tuple((sign, permutation) for sign in (1, -1) for permutation in PERMUTATIONS)
        if include_reflections else GEOMETRY.A2_LAYER_ISOMETRIES
    )
    for sign, permutation in isometries:
        transformed = [cell_from_vertices([
            tuple(sign * point[permutation[axis]] for axis in range(3))
            for point in cell_vertices(cell)
        ]) for cell in cells]
        key = tuple(sorted(cell_key(cell) for cell in transformed))
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "cells": transformed,
            "sign": sign,
            "permutation": list(permutation),
        })
    return result


def point_in_scaled_cell(point, source: dict, scale: int) -> bool:
    local = [point[axis] - scale * source["base"][axis] for axis in range(3)]
    a, b, c = source["order"]
    return 0 <= local[c] <= local[b] <= local[a] <= scale


def inflated_cells(cells: list[dict], scale: int) -> set[tuple[int, int, int, str]]:
    target = set()
    for source in cells:
        scaled_vertices = [tuple(scale * value for value in point)
                           for point in cell_vertices(source)]
        minima = [min(point[axis] for point in scaled_vertices) for axis in range(3)]
        maxima = [max(point[axis] for point in scaled_vertices) for axis in range(3)]
        for x in range(minima[0], maxima[0]):
            for y in range(minima[1], maxima[1]):
                for z in range(minima[2], maxima[2]):
                    for order in PERMUTATIONS:
                        candidate = {"base": [x, y, z], "order": list(order)}
                        if all(point_in_scaled_cell(point, source, scale)
                               for point in cell_vertices(candidate)):
                            target.add(cell_key(candidate))
    expected = len(cells) * scale ** 3
    if len(target) != expected:
        raise RuntimeError(f"inflated target has {len(target)} alcoves, expected {expected}")
    return target


def candidate_placements(target, orientations):
    placements = {}
    for orientation_index, orientation in enumerate(orientations):
        own = [cell_key(cell) for cell in orientation["cells"]]
        for target_cell in target:
            for own_cell in own:
                if own_cell[3] != target_cell[3]:
                    continue
                delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
                translated = frozenset((
                    cell[0] + delta[0], cell[1] + delta[1],
                    cell[2] + delta[2], cell[3]
                ) for cell in own)
                if translated.issubset(target) and translated not in placements:
                    placements[translated] = {
                        "orientation_index": orientation_index,
                        "translation": list(delta),
                        "cells": translated,
                    }
    return list(placements.values())


def first_atomically_uncovered(target, orientations):
    """Return a target alcove contained in no legal translated tile copy."""
    target_set = set(target)
    oriented = [[cell_key(cell) for cell in orientation["cells"]]
                for orientation in orientations]
    for target_cell in sorted(target):
        covered = False
        for own in oriented:
            for own_cell in own:
                if own_cell[3] != target_cell[3]:
                    continue
                delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
                if all((cell[0] + delta[0], cell[1] + delta[1],
                        cell[2] + delta[2], cell[3]) in target_set
                       for cell in own):
                    covered = True
                    break
            if covered:
                break
        if not covered:
            return target_cell
    return None


def screen(record: dict, scale: int, timeout_ms: int,
           include_reflections: bool = False) -> dict:
    cells = record["alcoves"]
    orientations = oriented_cells(cells, include_reflections)
    target = inflated_cells(cells, scale)
    atomic_uncovered = first_atomically_uncovered(target, orientations)
    if atomic_uncovered is not None:
        return {
            **record,
            "alcove_substitution_classification": "no_direct_scalar_substitution",
            "alcove_substitution": {
                "scale": scale,
                "target_alcoves": len(target),
                "expected_copies": scale ** 3,
                "include_reflections": include_reflections,
                "orientations": len(orientations),
                "placements_considered": 0,
                "nodes": 0,
                "failed_states": 0,
                "certified": True,
                "claim_scope": "direct_monotile_scalar_alcove_subdivision",
                "atomic_uncovered_alcove": list(atomic_uncovered),
                "independent_replay": {
                    "verified": True,
                    "method": "all_orientation_anchor_containment_scan",
                },
            },
        }
    placements = candidate_placements(target, orientations)
    solved = COVER.exact_cover(target, placements, timeout_ms)
    common = {
        "scale": scale,
        "target_alcoves": len(target),
        "expected_copies": scale ** 3,
        "include_reflections": include_reflections,
        "orientations": len(orientations),
        "placements_considered": len(placements),
        "nodes": solved["nodes"],
        "failed_states": solved["failed_states"],
    }
    if solved["result"] == "sat":
        replay = COVER.replay(target, placements, solved["solution"], scale ** 3)
        if not replay["verified"]:
            raise RuntimeError(f"substitution replay failed: {replay}")
        rule = [{
            "orientation_index": placements[index]["orientation_index"],
            "translation": placements[index]["translation"],
        } for index in solved["solution"]]
        return {
            **record,
            "alcove_substitution_classification": "substitution_rule",
            "alcove_substitution": {**common, "rule": rule, "replay": replay},
        }
    if solved["result"] == "unsat":
        return {
            **record,
            "alcove_substitution_classification": "no_direct_scalar_substitution",
            "alcove_substitution": {
                **common,
                "certified": True,
                "claim_scope": "direct_monotile_scalar_alcove_subdivision",
                "root_uncovered_alcove": solved["root_uncovered_cell"],
            },
        }
    return {
        **record,
        "alcove_substitution_classification": "unresolved",
        "alcove_substitution": {**common, "stopped_by": "time_limit"},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.scale < 2:
        parser.error("scale must be at least two")
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines()
               if line.strip()]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    counts: dict[str, int] = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.scale, args.timeout_ms,
                            args.include_reflections)
            classification = result["alcove_substitution_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
