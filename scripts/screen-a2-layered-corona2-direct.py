#!/usr/bin/env python3
"""Solve existence of a first corona and a compatible second corona jointly."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, Implies, Or, PbEq, PbLe, Solver, SolverFor, is_true, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")
CEGAR = load("a2_corona2_cegar", "screen-a2-layered-corona2-cegar.py")


def final_placement_universe(root, tile_orientations, first_placements):
    possible_support = set(root)
    for placement in first_placements:
        possible_support.update(placement["occupancy"])
    placements = {}
    for target_point in possible_support:
        for orientation_index, orientation in enumerate(tile_orientations):
            for own_point in orientation["occupancy"]:
                translation = tuple(target_point[axis] - own_point[axis] for axis in range(3))
                key = (orientation_index, translation)
                if key == (0, (0, 0, 0)) or key in placements:
                    continue
                occupancy = CORONA.translated_occupancy(orientation["occupancy"], translation)
                if any(root.get(point, 0) + weight > 48 for point, weight in occupancy.items()):
                    continue
                placements[key] = occupancy
    return [
        {
            "orientation_index": orientation_index,
            "translation": list(translation),
            "occupancy": occupancy,
        }
        for (orientation_index, translation), occupancy in placements.items()
    ]


def incidence(placements):
    result = {}
    for index, placement in enumerate(placements):
        for point, weight in placement["occupancy"].items():
            result.setdefault(point, []).append((index, weight))
    return result


def screen(record, timeout_ms, backend):
    started = time.monotonic()
    root = GEOMETRY.tile_occupancy(record["cells"])
    tile_orientations = GEOMETRY.orientations(root)
    first = CORONA.candidate_placements(root, tile_orientations)
    final = final_placement_universe(root, tile_orientations, first)
    first_variables = [Bool(f"first_{record['id']}_{index}") for index in range(len(first))]
    final_variables = [Bool(f"final_{record['id']}_{index}") for index in range(len(final))]
    first_incidence = incidence(first)
    final_incidence = incidence(final)
    final_index = {
        (placement["orientation_index"], tuple(placement["translation"])): index
        for index, placement in enumerate(final)
    }
    solver = SolverFor("QF_FD") if backend == "qffd" else Solver()
    solver.set(timeout=timeout_ms)

    # The first corona exactly saturates the root and never overfills elsewhere.
    for point, entries in first_incidence.items():
        terms = [(first_variables[index], weight) for index, weight in entries]
        capacity = 48 - root.get(point, 0)
        solver.add(PbEq(terms, capacity) if point in root else PbLe(terms, capacity))

    # Every first-corona placement persists in the final radius-two patch.
    for index, placement in enumerate(first):
        key = (placement["orientation_index"], tuple(placement["translation"]))
        solver.add(Implies(first_variables[index], final_variables[final_index[key]]))

    # The final patch never overfills and keeps the root saturated.
    for point, entries in final_incidence.items():
        terms = [(final_variables[index], weight) for index, weight in entries]
        capacity = 48 - root.get(point, 0)
        solver.add(PbEq(terms, capacity) if point in root else PbLe(terms, capacity))

    # Whichever first corona is selected determines the finite support that
    # must be saturated by the second corona.
    for point, entries in first_incidence.items():
        if point in root:
            continue
        active = Or([first_variables[index] for index, _weight in entries])
        final_terms = [(final_variables[index], weight) for index, weight in final_incidence[point]]
        solver.add(Implies(active, PbEq(final_terms, 48)))

    smt2 = solver.to_smt2()
    formula = {
        "backend": backend,
        "first_placements": len(first),
        "final_placements": len(final),
        "first_constraint_points": len(first_incidence),
        "final_constraint_points": len(final_incidence),
        "first_incidences": sum(map(len, first_incidence.values())),
        "final_incidences": sum(map(len, final_incidence.values())),
        "smt2_sha256": hashlib.sha256(smt2.encode()).hexdigest(),
    }
    result = solver.check()
    elapsed = round((time.monotonic() - started) * 1000)
    if result == sat:
        model = solver.model()
        first_indices = [
            index for index, variable in enumerate(first_variables)
            if is_true(model.eval(variable))
        ]
        final_indices = [
            index for index, variable in enumerate(final_variables)
            if is_true(model.eval(variable))
        ]
        first_patch = [{"orientation_index": 0, "translation": [0, 0, 0]}] + [
            {
                "orientation_index": first[index]["orientation_index"],
                "translation": first[index]["translation"],
            }
            for index in first_indices
        ]
        first_keys = {
            (placement["orientation_index"], tuple(placement["translation"]))
            for placement in first_patch
        }
        added = [
            {
                "orientation_index": final[index]["orientation_index"],
                "translation": final[index]["translation"],
            }
            for index in final_indices
            if (final[index]["orientation_index"], tuple(final[index]["translation"])) not in first_keys
        ]
        replay = CEGAR.replay_extension(tile_orientations, first_patch, added)
        if not replay["verified"]:
            raise RuntimeError(f"direct radius-two replay failed: {replay}")
        return {
            **record,
            "corona2_direct_classification": "radius2_witness",
            "corona2_direct": {
                **formula,
                "first_patch": first_patch,
                "added_patch": added,
                "replay": replay,
                "milliseconds": elapsed,
            },
        }
    if result == unsat:
        return {
            **record,
            "corona2_direct_classification": "radius2_unsat_needs_independent_replay",
            "corona2_direct": {**formula, "z3_unsat": True, "milliseconds": elapsed},
        }
    return {
        **record,
        "corona2_direct_classification": "unresolved",
        "corona2_direct": {
            **formula,
            "stopped_by": "solver_timeout",
            "milliseconds": elapsed,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--timeout-ms", type=int, default=300000)
    parser.add_argument("--backend", choices=("default", "qffd"), default="qffd")
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
            result = screen(record, args.timeout_ms, args.backend)
            classification = result["corona2_direct_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
