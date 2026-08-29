#!/usr/bin/env python3
"""CEGAR screen of first-corona witnesses against exact second-corona extension."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, Not, Or, PbEq, PbLe, Solver, is_true, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")


def placement_occupancy(tile_orientations, placement):
    return CORONA.translated_occupancy(
        tile_orientations[placement["orientation_index"]]["occupancy"],
        tuple(placement["translation"]),
    )


def patch_totals(tile_orientations, patch):
    totals = {}
    for placement in patch:
        for point, weight in placement_occupancy(tile_orientations, placement).items():
            totals[point] = totals.get(point, 0) + weight
            if totals[point] > 48:
                raise RuntimeError("stored patch overfills a lattice point")
    return totals


def build_weighted_solver(placements, existing_totals, exact_points, timeout_ms, prefix):
    variables = [Bool(f"{prefix}_{index}") for index in range(len(placements))]
    incidence = {}
    for index, placement in enumerate(placements):
        for point, weight in placement["occupancy"].items():
            incidence.setdefault(point, []).append((index, weight))
    solver = Solver()
    solver.set(timeout=timeout_ms)
    for point, entries in incidence.items():
        capacity = 48 - existing_totals.get(point, 0)
        terms = [(variables[index], weight) for index, weight in entries]
        solver.add(PbEq(terms, capacity) if point in exact_points else PbLe(terms, capacity))
    return solver, variables


def extension_candidates(tile_orientations, patch, totals):
    target = set(totals)
    selected = {
        (placement["orientation_index"], tuple(placement["translation"]))
        for placement in patch
    }
    candidates = {}
    for target_point in target:
        if totals[target_point] >= 48:
            continue
        for orientation_index, orientation in enumerate(tile_orientations):
            for own_point in orientation["occupancy"]:
                translation = tuple(target_point[axis] - own_point[axis] for axis in range(3))
                key = (orientation_index, translation)
                if key in selected or key in candidates:
                    continue
                occupancy = CORONA.translated_occupancy(orientation["occupancy"], translation)
                if any(totals.get(point, 0) + weight > 48 for point, weight in occupancy.items()):
                    continue
                candidates[key] = occupancy
    return [
        {
            "orientation_index": orientation_index,
            "translation": list(translation),
            "occupancy": occupancy,
        }
        for (orientation_index, translation), occupancy in candidates.items()
    ]


def replay_extension(tile_orientations, patch, added):
    before = patch_totals(tile_orientations, patch)
    target = set(before)
    after = dict(before)
    for placement in added:
        for point, weight in placement_occupancy(tile_orientations, placement).items():
            after[point] = after.get(point, 0) + weight
            if after[point] > 48:
                return {"verified": False, "reason": "overfill"}
    if any(after[point] != 48 for point in target):
        return {"verified": False, "reason": "first_corona_support_not_saturated"}
    return {
        "verified": True,
        "method": "independent_second_corona_replay",
        "target_points": len(target),
        "patch_copies": len(patch) + len(added),
        "occupied_points": len(after),
    }


def screen(record, trials, timeout_ms):
    started = time.monotonic()
    # Records may describe either ordinary lattice cells or exact affine-A3
    # alcove occupancy.  Keep the CEGAR geometry model identical to the
    # periodic and first-corona screens instead of silently requiring the
    # legacy ``cells`` representation.
    root = GEOMETRY.record_occupancy(record)
    tile_orientations = GEOMETRY.orientations(root)
    first_candidates = CORONA.candidate_placements(root, tile_orientations)
    outer, outer_variables = build_weighted_solver(
        first_candidates, root, set(root), timeout_ms, f"outer_{record['id']}"
    )
    obstructed = []
    for trial in range(trials):
        outer_result = outer.check()
        if outer_result == unsat:
            return {
                **record,
                "corona2_classification": "radius2_obstruction_exact",
                "corona2_cegar": {
                    "outer_exhausted": True,
                    "first_coronas_rejected": len(obstructed),
                    "trials": trial,
                    "milliseconds": round((time.monotonic() - started) * 1000),
                },
            }
        if outer_result != sat:
            break
        model = outer.model()
        first_indices = [index for index, variable in enumerate(outer_variables) if is_true(model.eval(variable))]
        first_patch = [{"orientation_index": 0, "translation": [0, 0, 0]}] + [
            {
                "orientation_index": first_candidates[index]["orientation_index"],
                "translation": list(first_candidates[index]["translation"]),
            }
            for index in first_indices
        ]
        totals = patch_totals(tile_orientations, first_patch)
        second_candidates = extension_candidates(tile_orientations, first_patch, totals)
        inner, inner_variables = build_weighted_solver(
            second_candidates, totals, set(totals), timeout_ms, f"inner_{record['id']}_{trial}"
        )
        inner_result = inner.check()
        if inner_result == sat:
            inner_model = inner.model()
            added = [
                {
                    "orientation_index": second_candidates[index]["orientation_index"],
                    "translation": second_candidates[index]["translation"],
                }
                for index, variable in enumerate(inner_variables)
                if is_true(inner_model.eval(variable))
            ]
            replay = replay_extension(tile_orientations, first_patch, added)
            if not replay["verified"]:
                raise RuntimeError(f"second-corona replay failed: {replay}")
            return {
                **record,
                "corona2_classification": "radius2_witness",
                "corona2_cegar": {
                    "outer_exhausted": False,
                    "first_coronas_rejected": len(obstructed),
                    "trial": trial + 1,
                    "first_patch": first_patch,
                    "added_patch": added,
                    "replay": replay,
                    "milliseconds": round((time.monotonic() - started) * 1000),
                },
            }
        if inner_result != unsat:
            break
        obstructed.append({
            "first_patch_copies": len(first_patch),
            "second_candidates": len(second_candidates),
        })
        # Exact-model blocking is deliberately conservative.  It never rules
        # out an untested first corona, unlike a heuristic generalized cut.
        outer.add(Or([
            Not(variable) if is_true(model.eval(variable)) else variable
            for variable in outer_variables
        ]))
    return {
        **record,
        "corona2_classification": "unresolved",
        "corona2_cegar": {
            "outer_exhausted": False,
            "first_coronas_rejected": len(obstructed),
            "configured_trials": trials,
            "milliseconds": round((time.monotonic() - started) * 1000),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    if requested:
        records = [record for record in records if record["id"] in requested]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.trials, args.timeout_ms)
            classification = result["corona2_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
