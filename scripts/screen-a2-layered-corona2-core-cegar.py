#!/usr/bin/env python3
"""Second-corona CEGAR with sound placement-subset UNSAT cores."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, Implies, Not, Or, PbEq, PbLe, Solver, SolverFor, is_true, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")
CEGAR = load("a2_corona2_cegar", "screen-a2-layered-corona2-cegar.py")


def incidence(placements):
    result = {}
    for index, placement in enumerate(placements):
        for point, weight in placement["occupancy"].items():
            result.setdefault(point, []).append((index, weight))
    return result


def extension_universe(root, tile_orientations, selected):
    support = set(root)
    for placement in selected:
        support.update(placement["occupancy"])
    placements = {}
    for target_point in support:
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


def extension_with_core(root, tile_orientations, selected, timeout_ms, prefix,
                        backend="z3"):
    final = extension_universe(root, tile_orientations, selected)
    final_index = {
        (placement["orientation_index"], tuple(placement["translation"])): index
        for index, placement in enumerate(final)
    }
    variables = [Bool(f"{prefix}_final_{index}") for index in range(len(final))]
    assumptions = [Bool(f"{prefix}_assume_{index}") for index in range(len(selected))]
    final_incidence = incidence(final)
    target_points = set(root)
    for placement in selected:
        target_points.update(placement["occupancy"])
    solver = SolverFor("QF_FD") if backend == "qffd" else Solver()
    solver.set(timeout=timeout_ms)
    exact_constraint = {}
    for point, entries in final_incidence.items():
        terms = [(variables[index], weight) for index, weight in entries]
        capacity = 48 - root.get(point, 0)
        if point in root:
            exact = PbEq(terms, capacity)
            solver.add(exact)
            exact_constraint[point] = exact
        else:
            solver.add(PbLe(terms, capacity))
            if point in target_points:
                exact_constraint[point] = PbEq(terms, capacity)
    for selected_index, placement in enumerate(selected):
        key = (placement["orientation_index"], tuple(placement["translation"]))
        assumption = assumptions[selected_index]
        solver.add(Implies(assumption, variables[final_index[key]]))
        for point in placement["occupancy"]:
            solver.add(Implies(assumption, exact_constraint[point]))
    result = solver.check(*assumptions)
    if result == sat:
        model = solver.model()
        final_selected = [
            index for index, variable in enumerate(variables)
            if is_true(model.eval(variable))
        ]
        return {
            "result": "sat",
            "final": final,
            "selected": final_selected,
            "placements_considered": len(final),
        }
    if result == unsat:
        core_names = {str(item) for item in solver.unsat_core()}
        core = [index for index, assumption in enumerate(assumptions) if str(assumption) in core_names]
        return {
            "result": "unsat",
            "core": core,
            "placements_considered": len(final),
        }
    return {"result": "unknown", "placements_considered": len(final)}


def screen(
    record, maximum_rounds, timeout_ms, max_first_copies=0, seed_clauses=None,
    checkpoint_callback=None, seed_rounds=0, seed_milliseconds=0,
    outer_solver_kind="z3", inner_solver_kind="z3",
):
    started = time.monotonic()
    root = GEOMETRY.record_occupancy(record)
    tile_orientations = GEOMETRY.orientations(root)
    first = CORONA.candidate_placements(root, tile_orientations)
    outer_variables = [Bool(f"outer_{record['id']}_{index}") for index in range(len(first))]
    outer = SolverFor("QF_FD") if outer_solver_kind == "qffd" else Solver()
    outer.set(timeout=timeout_ms)
    for point, entries in incidence(first).items():
        terms = [(outer_variables[index], weight) for index, weight in entries]
        capacity = 48 - root.get(point, 0)
        outer.add(PbEq(terms, capacity) if point in root else PbLe(terms, capacity))
    if max_first_copies > 0:
        outer.add(PbLe([(variable, 1) for variable in outer_variables], max_first_copies - 1))
    clauses = []
    for seed in seed_clauses or []:
        indices = seed["outer_placement_indices"]
        if not indices:
            raise ValueError("seed core must not be empty")
        outer.add(Or([Not(outer_variables[index]) for index in indices]))
        clauses.append({
            "outer_placement_indices": indices,
            "size": len(indices),
            "seeded": True,
            "source": seed.get("source"),
        })

    def progress_metadata(completed_rounds):
        """Keep continuation and cumulative effort distinct in every report."""
        elapsed = round((time.monotonic() - started) * 1000)
        return {
            "rounds": seed_rounds + completed_rounds,
            "seed_rounds": seed_rounds,
            "continuation_rounds": completed_rounds,
            "milliseconds": elapsed,
            "seed_milliseconds": seed_milliseconds,
            "cumulative_milliseconds": seed_milliseconds + elapsed,
        }

    def checkpoint(stopped_by="in_progress"):
        if checkpoint_callback is None:
            return
        checkpoint_callback({
            **record,
            "corona2_core_classification": "unresolved",
            "corona2_core_cegar": {
                "outer_exhausted": False,
                **progress_metadata(max(0, len(clauses) - len(seed_clauses or []))),
                "max_first_copies": max_first_copies or None,
                "clauses": clauses,
                "stopped_by": stopped_by,
            },
        })

    checkpoint()
    for round_index in range(maximum_rounds):
        outer_result = outer.check()
        if outer_result == unsat:
            return {
                **record,
                "corona2_core_classification": "radius2_obstruction_z3",
                "corona2_core_cegar": {
                    "outer_exhausted": True,
                    **progress_metadata(round_index),
                    "max_first_copies": max_first_copies or None,
                    "clauses": clauses,
                },
            }
        if outer_result != sat:
            break
        outer_model = outer.model()
        first_indices = [
            index for index, variable in enumerate(outer_variables)
            if is_true(outer_model.eval(variable))
        ]
        selected = [first[index] for index in first_indices]
        extension = extension_with_core(
            root, tile_orientations, selected, timeout_ms,
            f"inner_{record['id']}_{round_index}", inner_solver_kind
        )
        if extension["result"] == "sat":
            first_patch = [{"orientation_index": 0, "translation": [0, 0, 0]}] + [
                {
                    "orientation_index": placement["orientation_index"],
                    "translation": placement["translation"],
                }
                for placement in selected
            ]
            first_keys = {
                (placement["orientation_index"], tuple(placement["translation"]))
                for placement in first_patch
            }
            added = [
                {
                    "orientation_index": extension["final"][index]["orientation_index"],
                    "translation": extension["final"][index]["translation"],
                }
                for index in extension["selected"]
                if (
                    extension["final"][index]["orientation_index"],
                    tuple(extension["final"][index]["translation"])
                ) not in first_keys
            ]
            replay = CEGAR.replay_extension(tile_orientations, first_patch, added)
            if not replay["verified"]:
                raise RuntimeError(f"core CEGAR witness replay failed: {replay}")
            return {
                **record,
                "corona2_core_classification": "radius2_witness",
                "corona2_core_cegar": {
                    "outer_exhausted": False,
                    **progress_metadata(round_index + 1),
                    "max_first_copies": max_first_copies or None,
                    "clauses": clauses,
                    "first_patch": first_patch,
                    "added_patch": added,
                    "replay": replay,
                },
            }
        if extension["result"] != "unsat":
            break
        core_outer_indices = [first_indices[index] for index in extension["core"]]
        if not core_outer_indices:
            raise RuntimeError("empty second-corona UNSAT core")
        outer.add(Or([Not(outer_variables[index]) for index in core_outer_indices]))
        clauses.append({
            "outer_placement_indices": core_outer_indices,
            "size": len(core_outer_indices),
            "first_patch_copies": 1 + len(first_indices),
            "extension_placements_considered": extension["placements_considered"],
        })
        checkpoint()
    return {
        **record,
        "corona2_core_classification": "unresolved",
        "corona2_core_cegar": {
            "outer_exhausted": False,
            **progress_metadata(max(0, len(clauses) - len(seed_clauses or []))),
            "max_first_copies": max_first_copies or None,
            "clauses": clauses,
            "stopped_by": (
                "round_limit"
                if max(0, len(clauses) - len(seed_clauses or [])) == maximum_rounds
                else "solver_timeout"
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument(
        "--only-corona-witnesses",
        action="store_true",
        help="skip rows whose first corona has not been independently replayed",
    )
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=64)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--max-first-copies", type=int, default=0)
    parser.add_argument("--seed-core", action="append", default=[])
    parser.add_argument("--only-seeded", action="store_true")
    parser.add_argument("--checkpoint-dir", default="")
    parser.add_argument("--outer-solver", choices=("z3", "qffd"), default="z3")
    parser.add_argument("--inner-solver", choices=("z3", "qffd"), default="z3")
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    if requested:
        records = [record for record in records if record["id"] in requested]
    if args.only_corona_witnesses:
        records = [
            record for record in records
            if record.get("corona_classification") == "root_corona_exists"
            and record.get("corona_z3", {}).get("replay", {}).get("verified") is True
        ]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    seeds_by_id = {}
    seed_effort_by_id = {}
    for seed_core_path in args.seed_core:
        for line in Path(seed_core_path).read_text().splitlines():
            if not line.strip():
                continue
            seed = json.loads(line)
            seed_report = seed.get("corona2_core_cegar", {})
            previous = seed_effort_by_id.get(seed["id"], (0, 0))
            seed_effort_by_id[seed["id"]] = (
                max(previous[0], seed_report.get("rounds", 0)),
                max(
                    previous[1],
                    seed_report.get(
                        "cumulative_milliseconds",
                        seed_report.get("milliseconds", 0),
                    ),
                ),
            )
            if "reduced_outer_placement_indices" in seed:
                indices_list = [seed["reduced_outer_placement_indices"]]
            elif seed.get("retained_corona_extension_classification") == "retained_corona_unextendible":
                indices_list = [seed["retained_corona_extension"]["outer_placement_indices"]]
            elif "corona2_core_cegar" not in seed:
                continue
            else:
                indices_list = [
                    clause["outer_placement_indices"]
                    for clause in seed["corona2_core_cegar"]["clauses"]
                ]
            for indices in indices_list:
                seeds_by_id.setdefault(seed["id"], []).append({
                    "outer_placement_indices": indices,
                    "source": seed_core_path,
                })
    for candidate_id, seeds in seeds_by_id.items():
        canonical = []
        seen = set()
        for seed in sorted(seeds, key=lambda item: len(item["outer_placement_indices"])):
            key = frozenset(seed["outer_placement_indices"])
            if key in seen or any(existing.issubset(key) for existing, _ in canonical):
                continue
            canonical.append((key, seed))
            seen.add(key)
        seeds_by_id[candidate_id] = [seed for _, seed in canonical]
    if args.only_seeded:
        records = [record for record in records if record["id"] in seeds_by_id]
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            checkpoint_dir = Path(args.checkpoint_dir) if args.checkpoint_dir else output.parent
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_path = checkpoint_dir / f"{output.stem}.{record['id']}.checkpoint.ndjson"
            def save_checkpoint(value, path=checkpoint_path):
                path.write_text(json.dumps(value, separators=(",", ":")) + "\n")
            result = screen(
                record, args.rounds, args.timeout_ms, args.max_first_copies,
                seeds_by_id.get(record["id"], []),
                save_checkpoint,
                *seed_effort_by_id.get(record["id"], (0, 0)),
                args.outer_solver, args.inner_solver,
            )
            classification = result["corona2_core_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
