#!/usr/bin/env python3
"""Exact scalar-inflation substitution screen for A2 layered polyprisms."""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import time
from pathlib import Path

from z3 import Bool, PbEq, Solver, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")


def cell_key(cell):
    return cell["q"], cell["r"], cell["k"], cell["kind"]


def cell_from_vertices(vertices):
    sums = [sum(point) for point in vertices]
    base_sum = min(sums)
    if base_sum % 3 or max(sums) - base_sum != 3:
        raise ValueError("transformed cell left the A2 prism honeycomb")
    k = base_sum // 3
    base = [
        (point[0] - k, point[1] - k)
        for point, layer_sum in zip(vertices, sums)
        if layer_sum == base_sum
    ]
    q = min(point[0] for point in base)
    r = min(point[1] for point in base)
    kind = "u" if (q, r) in base else "d"
    return {"q": q, "r": r, "k": k, "kind": kind}


def oriented_cells(cells):
    result = []
    seen = set()
    for sign, permutation in GEOMETRY.A2_LAYER_ISOMETRIES:
        transformed = []
        for cell in cells:
            vertices = [
                tuple(sign * point[permutation[axis]] for axis in range(3))
                for point in GEOMETRY.cell_vertices(cell)
            ]
            transformed.append(cell_from_vertices(vertices))
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


def inside_triangle(px3, py3, triangle):
    vertices = [(3 * x, 3 * y) for x, y in triangle]
    crosses = []
    for index in range(3):
        ax, ay = vertices[index]
        bx, by = vertices[(index + 1) % 3]
        crosses.append((bx - ax) * (py3 - ay) - (by - ay) * (px3 - ax))
    return all(value >= 0 for value in crosses) or all(value <= 0 for value in crosses)


def scaled_cells(cells, scale):
    target = set()
    for cell in cells:
        base = GEOMETRY.cell_vertices(cell)[:3]
        k = cell["k"]
        triangle = [((point[0] - k) * scale, (point[1] - k) * scale) for point in base]
        min_q = min(point[0] for point in triangle) - 1
        max_q = max(point[0] for point in triangle)
        min_r = min(point[1] for point in triangle) - 1
        max_r = max(point[1] for point in triangle)
        for sub_k in range(scale * k, scale * (k + 1)):
            for q in range(min_q, max_q + 1):
                for r in range(min_r, max_r + 1):
                    for kind, offset in (("u", 1), ("d", 2)):
                        if inside_triangle(3 * q + offset, 3 * r + offset, triangle):
                            target.add((q, r, sub_k, kind))
    expected = len(cells) * scale ** 3
    if len(target) != expected:
        raise RuntimeError(f"scaled target has {len(target)} cells, expected {expected}")
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
                translated = frozenset(
                    (
                        cell[0] + delta[0], cell[1] + delta[1],
                        cell[2] + delta[2], cell[3],
                    )
                    for cell in own
                )
                if translated.issubset(target) and translated not in placements:
                    placements[translated] = {
                        "orientation_index": orientation_index,
                        "translation": list(delta),
                        "cells": translated,
                    }
    return list(placements.values())


def exact_cover(target, placements, timeout_ms):
    ordered_target = sorted(target)
    target_index = {cell: index for index, cell in enumerate(ordered_target)}
    masks = [sum(1 << target_index[cell] for cell in placement["cells"]) for placement in placements]
    by_cell = [[] for _ in ordered_target]
    for placement_index, mask in enumerate(masks):
        for cell_index in itertools.compress(range(len(ordered_target)), ((mask >> i) & 1 for i in range(len(ordered_target)))):
            by_cell[cell_index].append(placement_index)
    all_cells = (1 << len(ordered_target)) - 1
    deadline = time.monotonic() + timeout_ms / 1000
    failed = set()
    nodes = 0
    timed_out = False
    root_uncovered = None

    def visit(remaining):
        nonlocal nodes, timed_out, root_uncovered
        nodes += 1
        if not remaining:
            return []
        if time.monotonic() >= deadline:
            timed_out = True
            return None
        if remaining in failed:
            return None
        active = []
        bits = remaining
        while bits:
            lowest = bits & -bits
            cell_index = lowest.bit_length() - 1
            legal = [index for index in by_cell[cell_index] if masks[index] & ~remaining == 0]
            if not legal:
                if remaining == all_cells:
                    root_uncovered = ordered_target[cell_index]
                failed.add(remaining)
                return None
            active.append((len(legal), cell_index, legal))
            bits ^= lowest
        _, _, legal = min(active)
        for placement_index in legal:
            suffix = visit(remaining ^ masks[placement_index])
            if suffix is not None:
                return [placement_index, *suffix]
            if timed_out:
                return None
        failed.add(remaining)
        return None

    solution = visit(all_cells)
    return {
        "result": "unknown" if timed_out else ("sat" if solution is not None else "unsat"),
        "solution": solution,
        "nodes": nodes,
        "failed_states": len(failed),
        "root_uncovered_cell": list(root_uncovered) if root_uncovered else None,
    }


def replay(target, placements, solution, expected_copies):
    covered = set()
    for index in solution:
        cells = placements[index]["cells"]
        if covered.intersection(cells):
            return {"verified": False, "reason": "overlap"}
        covered.update(cells)
    if covered != target:
        return {"verified": False, "reason": "target_mismatch"}
    if len(solution) != expected_copies:
        return {"verified": False, "reason": "copy_count_mismatch"}
    return {
        "verified": True,
        "method": "independent_atomic_a2_cell_exact_cover",
        "target_cells": len(target),
        "patch_copies": len(solution),
    }


def replay_local_obstruction(target, orientations, target_cell):
    target_cell = tuple(target_cell)
    placements_checked = 0
    for orientation in orientations:
        own = [cell_key(cell) for cell in orientation["cells"]]
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
                    "reason": "covering_placement_exists",
                    "placements_checked": placements_checked,
                }
    return {
        "verified": True,
        "method": "independent_all_orientations_all_anchors_local_obstruction",
        "uncovered_cell": list(target_cell),
        "placements_checked": placements_checked,
    }


def replay_unsat_with_z3(target, placements, timeout_ms):
    variables = [Bool(f"sub_replay_{index}") for index in range(len(placements))]
    incidence = {cell: [] for cell in target}
    for index, placement in enumerate(placements):
        for cell in placement["cells"]:
            incidence[cell].append(index)
    solver = Solver()
    solver.set(timeout=timeout_ms)
    for cell in sorted(target):
        solver.add(PbEq([(variables[index], 1) for index in incidence[cell]], 1))
    result = solver.check()
    return {
        "verified": result == unsat,
        "method": "independent_z3_atomic_exact_cover",
        "result": "unsat" if result == unsat else ("sat" if result == sat else "unknown"),
        "variables": len(variables),
        "constraints": len(target),
    }


def screen(record, scale, timeout_ms):
    started = time.monotonic()
    orientations = oriented_cells(record["cells"])
    target = scaled_cells(record["cells"], scale)
    placements = candidate_placements(target, orientations)
    solved = exact_cover(target, placements, timeout_ms)
    common = {
        "scale": scale,
        "inflation_matrix": [[scale, 0, 0], [0, scale, 0], [0, 0, scale]],
        "target_cells": len(target),
        "orientations": len(orientations),
        "placements_considered": len(placements),
        "nodes": solved["nodes"],
        "failed_states": solved["failed_states"],
        "milliseconds": round((time.monotonic() - started) * 1000),
    }
    if solved["result"] == "sat":
        expected_copies = scale ** 3
        verification = replay(target, placements, solved["solution"], expected_copies)
        if not verification["verified"]:
            raise RuntimeError(f"substitution replay failed: {verification}")
        patch = [
            {
                "orientation_index": placements[index]["orientation_index"],
                "translation": placements[index]["translation"],
            }
            for index in solved["solution"]
        ]
        return {
            **record,
            "substitution_classification": "scalar_substitution_rule",
            "substitution": {
                **common,
                "certified": True,
                "can_tile": True,
                "patch": patch,
                "replay": verification,
            },
        }
    obstruction_replay = None
    if solved["result"] == "unsat" and solved["root_uncovered_cell"] is not None:
        obstruction_replay = replay_local_obstruction(
            target, orientations, solved["root_uncovered_cell"]
        )
        if not obstruction_replay["verified"]:
            raise RuntimeError(f"substitution obstruction replay failed: {obstruction_replay}")
    exact_unsat_replay = None
    if solved["result"] == "unsat" and obstruction_replay is None:
        exact_unsat_replay = replay_unsat_with_z3(target, placements, timeout_ms)
        if not exact_unsat_replay["verified"]:
            raise RuntimeError(f"substitution UNSAT replay failed: {exact_unsat_replay}")
    return {
        **record,
        "substitution_classification": (
            "no_scalar_substitution_at_scale" if solved["result"] == "unsat" else "unresolved"
        ),
        "substitution": {
            **common,
            "certified": solved["result"] == "unsat",
            "can_tile": None,
            "stopped_by": None if solved["result"] == "unsat" else "time_limit",
            "local_obstruction_replay": obstruction_replay,
            "exact_unsat_replay": exact_unsat_replay,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    parser.add_argument("--ids", default="")
    args = parser.parse_args()
    if args.scale < 2:
        parser.error("scale must be at least two")
    requested = {value for value in args.ids.split(",") if value}
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    if requested:
        records = [record for record in records if record["id"] in requested]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.scale, args.timeout_ms)
            classification = result["substitution_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
