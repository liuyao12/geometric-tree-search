#!/usr/bin/env python3
"""Exact root-corona screen for A2 layered lattice functions."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, PbEq, PbLe, Solver, is_true, sat, unsat


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_periodic_z3",
    ROOT / "scripts" / "screen-a2-layered-periodic-z3.py",
)
GEOMETRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEOMETRY)


def translated_occupancy(occupancy, translation):
    return {
        tuple(point[axis] + translation[axis] for axis in range(3)): weight
        for point, weight in occupancy.items()
    }


def candidate_placements(root, tile_orientations):
    placements = {}
    for orientation_index, orientation in enumerate(tile_orientations):
        for root_point in root:
            for own_point in orientation["occupancy"]:
                translation = tuple(root_point[axis] - own_point[axis] for axis in range(3))
                if orientation_index == 0 and translation == (0, 0, 0):
                    continue
                occupancy = translated_occupancy(orientation["occupancy"], translation)
                if any(root.get(point, 0) + weight > 48 for point, weight in occupancy.items()):
                    continue
                placements[(orientation_index, translation)] = occupancy
    return [
        {
            "orientation_index": orientation_index,
            "translation": translation,
            "occupancy": occupancy,
        }
        for (orientation_index, translation), occupancy in placements.items()
    ]


def replay_corona(root, placements, witness):
    totals = dict(root)
    for index in witness:
        for point, weight in placements[index]["occupancy"].items():
            totals[point] = totals.get(point, 0) + weight
            if totals[point] > 48:
                return {"verified": False, "reason": "overfill", "point": point}
    unsaturated = [point for point in root if totals.get(point, 0) != 48]
    if unsaturated:
        return {"verified": False, "reason": "root_not_saturated", "points": unsaturated}
    return {
        "verified": True,
        "method": "independent_weighted_corona_replay",
        "root_points": len(root),
        "patch_copies": 1 + len(witness),
        "occupied_points": len(totals),
    }


def screen(record, timeout_ms):
    started = time.monotonic()
    root = GEOMETRY.tile_occupancy(record["cells"])
    tile_orientations = GEOMETRY.orientations(root)
    placements = candidate_placements(root, tile_orientations)
    variables = [Bool(f"corona_{record['id']}_{index}") for index in range(len(placements))]
    incidence = {}
    for index, placement in enumerate(placements):
        for point, weight in placement["occupancy"].items():
            incidence.setdefault(point, []).append((index, weight))
    solver = Solver()
    solver.set(timeout=timeout_ms)
    for point, entries in incidence.items():
        terms = [(variables[index], weight) for index, weight in entries]
        if point in root:
            solver.add(PbEq(terms, 48 - root[point]))
        else:
            solver.add(PbLe(terms, 48))
    smt2 = solver.to_smt2()
    result = solver.check()
    common = {
        "placements_considered": len(placements),
        "constraint_points": len(incidence),
        "smt2_sha256": hashlib.sha256(smt2.encode()).hexdigest(),
        "milliseconds": round((time.monotonic() - started) * 1000),
    }
    if result == sat:
        model = solver.model()
        witness = [index for index, variable in enumerate(variables) if is_true(model.eval(variable))]
        replay = replay_corona(root, placements, witness)
        if not replay["verified"]:
            raise RuntimeError(f"corona replay failed: {replay}")
        return {
            **record,
            "corona_classification": "root_corona_exists",
            "corona_z3": {
                **common,
                "witness": [
                    {
                        "orientation_index": placements[index]["orientation_index"],
                        "translation": list(placements[index]["translation"]),
                    }
                    for index in witness
                ],
                "replay": replay,
            },
        }
    if result == unsat:
        return {
            **record,
            "corona_classification": "root_corona_unsat_needs_independent_replay",
            "corona_z3": {**common, "z3_unsat": True},
        }
    return {
        **record,
        "corona_classification": "unresolved",
        "corona_z3": {**common, "stopped_by": "solver_timeout"},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--only-unresolved", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    if args.only_unresolved:
        records = [record for record in records if record.get("classification") == "unresolved"]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.timeout_ms)
            classification = result["corona_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
