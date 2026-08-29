#!/usr/bin/env python3
"""Exact hierarchical GCTS from root coronas through radius three.

The outer solver enumerates first coronas.  A middle solver enumerates complete
radius-two extensions of each first corona.  Exact radius-three failures return
assumption cores to the middle solver; exhaustion there returns a smaller core
to the outer solver.  Every learned clause is therefore a replayable logical
consequence, not a heuristic pruning rule.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, BoolVal, Implies, Not, Or, PbEq, PbLe, Solver, SolverFor, is_true, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")
CEGAR = load("a2_corona2_cegar", "screen-a2-layered-corona2-cegar.py")
CORE = load("a2_corona2_core", "screen-a2-layered-corona2-core-cegar.py")


def key(placement: dict) -> tuple[int, tuple[int, int, int]]:
    return placement["orientation_index"], tuple(placement["translation"])


def serialized_clause(keys) -> list[dict]:
    return [
        {"orientation_index": orientation, "translation": list(translation)}
        for orientation, translation in sorted(set(keys))
    ]


def clause_signature(keys) -> tuple:
    return tuple(sorted(set(keys)))


def make_solver(kind: str, timeout_ms: int):
    solver = SolverFor("QF_FD") if kind == "qffd" else Solver()
    solver.set(timeout=timeout_ms)
    return solver


def outer_solver(root, first, timeout_ms: int, backend: str, clauses):
    variables = [Bool(f"radius3_outer_{index}") for index in range(len(first))]
    solver = make_solver(backend, timeout_ms)
    for point, entries in CORE.incidence(first).items():
        terms = [(variables[index], weight) for index, weight in entries]
        capacity = 48 - root.get(point, 0)
        solver.add(PbEq(terms, capacity) if point in root else PbLe(terms, capacity))
    index_by_key = {key(placement): index for index, placement in enumerate(first)}
    for clause in clauses:
        indices = [index_by_key[item] for item in clause if item in index_by_key]
        if len(indices) == len(clause):
            solver.add(Or([Not(variables[index]) for index in indices]) if indices else BoolVal(False))
    return solver, variables


def middle_solver(root, orientations, selected_first, timeout_ms: int, backend: str,
                  learned_radius2_clauses):
    final = CORE.extension_universe(root, orientations, selected_first)
    variables = [Bool(f"radius3_middle_{index}") for index in range(len(final))]
    assumptions = [Bool(f"radius3_middle_assume_{index}")
                   for index in range(len(selected_first))]
    solver = make_solver(backend, timeout_ms)
    incidence = CORE.incidence(final)
    target_points = set(root)
    for placement in selected_first:
        target_points.update(placement["occupancy"])
    exact_constraint = {}
    for point, entries in incidence.items():
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
    index_by_key = {key(placement): index for index, placement in enumerate(final)}
    for selected_index, placement in enumerate(selected_first):
        placement_key = key(placement)
        assumption = assumptions[selected_index]
        solver.add(Implies(assumption, variables[index_by_key[placement_key]]))
        for point in placement["occupancy"]:
            solver.add(Implies(assumption, exact_constraint[point]))
    for clause in learned_radius2_clauses:
        indices = [index_by_key[item] for item in clause if item in index_by_key]
        if len(indices) == len(clause):
            solver.add(Or([Not(variables[index]) for index in indices]) if indices else BoolVal(False))
    return solver, variables, assumptions, final


def exact_patch_extension(root, orientations, selected, timeout_ms: int, max_nodes: int):
    """Complete sparse-capacity GCTS for one fixed source patch.

    Unlike the SMT formulation, construction is linear in the sparse
    incidence list.  On exact exhaustion the whole fixed source patch is a
    sound (if deliberately non-minimal) failure core.
    """
    final = CORE.extension_universe(root, orientations, selected)
    fixed_keys = {key(placement) for placement in selected}
    totals = dict(root)
    for placement in selected:
        for point, weight in placement["occupancy"].items():
            totals[point] = totals.get(point, 0) + weight
            if totals[point] > 48:
                raise RuntimeError("fixed radius-two patch overfills a lattice point")
    candidates = [placement for placement in final if key(placement) not in fixed_keys]
    points = sorted(set(totals).union(
        point for placement in candidates for point in placement["occupancy"]
    ))
    point_index = {point: index for index, point in enumerate(points)}
    target_indices = [point_index[point] for point in totals]
    target_set = set(target_indices)
    capacities = [48 - totals.get(point, 0) for point in points]
    encoded = []
    by_target = [[] for _ in points]
    for candidate_index, placement in enumerate(candidates):
        entries = tuple((point_index[point], weight)
                        for point, weight in placement["occupancy"].items())
        if any(weight > capacities[index] for index, weight in entries):
            encoded.append(())
            continue
        encoded.append(entries)
        for index, weight in entries:
            if index in target_set and weight:
                by_target[index].append(candidate_index)
    nodes = 0
    failed = set()
    chosen = []
    cutoff = False
    deadline = time.monotonic() + timeout_ms / 1000

    def search(unavailable_mask: int):
        nonlocal nodes, cutoff
        if (max_nodes and nodes >= max_nodes) or time.monotonic() >= deadline:
            cutoff = True
            return None
        nodes += 1
        if all(capacities[index] == 0 for index in target_indices):
            return tuple(chosen)
        state = (bytes(capacities), unavailable_mask)
        if state in failed:
            return None
        best_candidates = None
        for target_index in target_indices:
            if capacities[target_index] == 0:
                continue
            fitting = []
            for candidate_index in by_target[target_index]:
                bit = 1 << candidate_index
                if unavailable_mask & bit:
                    continue
                entries = encoded[candidate_index]
                if entries and all(weight <= capacities[index] for index, weight in entries):
                    fitting.append(candidate_index)
            if not fitting:
                failed.add(state)
                return None
            if best_candidates is None or len(fitting) < len(best_candidates):
                best_candidates = fitting
        skipped = 0
        for candidate_index in best_candidates:
            bit = 1 << candidate_index
            entries = encoded[candidate_index]
            for index, weight in entries:
                capacities[index] -= weight
            chosen.append(candidate_index)
            witness = search(unavailable_mask | skipped | bit)
            if witness is not None:
                return witness
            chosen.pop()
            for index, weight in entries:
                capacities[index] += weight
            if cutoff:
                return None
            skipped |= bit
        failed.add(state)
        return None

    witness = search(0)
    return {
        "result": "sat" if witness is not None else ("unknown" if cutoff else "unsat"),
        "added": [candidates[index] for index in (witness or ())],
        "nodes": nodes,
        "failed_states": len(failed),
        "placements_considered": len(final),
        "method": "exact_sparse_capacity_gcts_mrv",
    }


def search_middle(root, orientations, selected_first, timeout_ms, backend,
                  maximum_middle_rounds, learned_radius2_clauses, learned_signatures,
                  prefix, inner_node_limit):
    solver, variables, assumptions, final = middle_solver(
        root, orientations, selected_first, timeout_ms, backend, learned_radius2_clauses
    )
    for middle_round in range(maximum_middle_rounds):
        result = solver.check(*assumptions)
        if result == unsat:
            core_names = {str(item) for item in solver.unsat_core()}
            outer_core = [index for index, assumption in enumerate(assumptions)
                          if str(assumption) in core_names]
            return {"result": "exhausted", "outer_core": outer_core,
                    "middle_rounds": middle_round}
        if result != sat:
            return {"result": "unknown", "middle_rounds": middle_round,
                    "stopped_by": "middle_solver_timeout"}
        model = solver.model()
        selected_indices = [index for index, variable in enumerate(variables)
                            if is_true(model.eval(variable))]
        selected = [final[index] for index in selected_indices]
        extension = exact_patch_extension(
            root, orientations, selected, timeout_ms, inner_node_limit
        )
        if extension["result"] == "sat":
            radius2_patch = [{"orientation_index": 0, "translation": [0, 0, 0]}] + [
                {"orientation_index": placement["orientation_index"],
                 "translation": placement["translation"]}
                for placement in selected
            ]
            radius2_keys = {key(placement) for placement in radius2_patch}
            added = [
                {"orientation_index": placement["orientation_index"],
                 "translation": placement["translation"]}
                for placement in extension["added"]
                if key(placement) not in radius2_keys
            ]
            replay = CEGAR.replay_extension(orientations, radius2_patch, added)
            if not replay["verified"]:
                raise RuntimeError(f"radius-three replay failed: {replay}")
            return {
                "result": "witness",
                "middle_rounds": middle_round + 1,
                "radius2_patch": radius2_patch,
                "added_patch": added,
                "replay": replay,
            }
        if extension["result"] != "unsat":
            return {"result": "unknown", "middle_rounds": middle_round + 1,
                    "stopped_by": "radius3_solver_timeout"}
        # Exact sparse exhaustion proves failure of this entire selected
        # radius-two patch.  Using the full patch as a clause is sound and
        # avoids the enormous SMT construction formerly needed for a smaller
        # assumption core.
        core_keys = [key(placement) for placement in selected]
        if not core_keys:
            raise RuntimeError("empty radius-three failure core")
        signature = clause_signature(core_keys)
        indices = [{key(placement): index for index, placement in enumerate(final)}[item]
                   for item in signature]
        solver.add(Or([Not(variables[index]) for index in indices]))
        if signature not in learned_signatures:
            learned_signatures.add(signature)
            learned_radius2_clauses.append(signature)
    return {"result": "budget", "middle_rounds": maximum_middle_rounds,
            "stopped_by": "middle_round_limit"}


def decoded_clauses(items) -> list[tuple]:
    return [clause_signature(
        (item["orientation_index"], tuple(item["translation"])) for item in clause
    ) for clause in items]


def screen(record: dict, maximum_outer_rounds: int, maximum_middle_rounds: int,
           timeout_ms: int, backend: str, seed: dict | None = None,
           inner_node_limit: int = 500000) -> dict:
    started = time.monotonic()
    root = GEOMETRY.record_occupancy(record)
    orientations = GEOMETRY.orientations(root)
    first = CORONA.candidate_placements(root, orientations)
    seed_receipt = (seed or {}).get("radius3_gcts", {})
    radius2_clauses = decoded_clauses(seed_receipt.get("radius2_failure_clauses", []))
    radius2_signatures = set(radius2_clauses)
    outer_clauses = decoded_clauses(seed_receipt.get("first_corona_failure_clauses", []))
    outer_signatures = set(outer_clauses)
    seed_outer_rounds = int(seed_receipt.get("outer_rounds", 0))
    seed_middle_rounds = int(seed_receipt.get("middle_rounds", 0))
    seed_milliseconds = int(seed_receipt.get("cumulative_milliseconds",
                                               seed_receipt.get("milliseconds", 0)))
    outer, outer_variables = outer_solver(root, first, timeout_ms, backend, outer_clauses)
    total_middle_rounds = 0
    for outer_round in range(maximum_outer_rounds):
        result = outer.check()
        if result == unsat:
            return {
                **record,
                "radius3_gcts_classification": "radius3_obstruction_exact",
                "radius3_gcts": {
                    "outer_exhausted": True,
                    "outer_rounds": seed_outer_rounds + outer_round,
                    "continuation_outer_rounds": outer_round,
                    "middle_rounds": seed_middle_rounds + total_middle_rounds,
                    "continuation_middle_rounds": total_middle_rounds,
                    "radius2_failure_clauses": [serialized_clause(clause)
                                                for clause in radius2_clauses],
                    "first_corona_failure_clauses": [serialized_clause(clause)
                                                     for clause in outer_clauses],
                    "milliseconds": round((time.monotonic() - started) * 1000),
                    "seed_milliseconds": seed_milliseconds,
                    "cumulative_milliseconds": seed_milliseconds + round(
                        (time.monotonic() - started) * 1000),
                },
            }
        if result != sat:
            stopped_by = "outer_solver_timeout"
            break
        model = outer.model()
        first_indices = [index for index, variable in enumerate(outer_variables)
                         if is_true(model.eval(variable))]
        selected_first = [first[index] for index in first_indices]
        middle = search_middle(
            root, orientations, selected_first, timeout_ms, backend,
            maximum_middle_rounds, radius2_clauses, radius2_signatures,
            f"radius3_{record['id']}_{outer_round}", inner_node_limit,
        )
        total_middle_rounds += middle["middle_rounds"]
        if middle["result"] == "witness":
            return {
                **record,
                "radius3_gcts_classification": "radius3_witness",
                "radius3_gcts": {
                    "outer_exhausted": False,
                    "outer_rounds": seed_outer_rounds + outer_round + 1,
                    "continuation_outer_rounds": outer_round + 1,
                    "middle_rounds": seed_middle_rounds + total_middle_rounds,
                    "continuation_middle_rounds": total_middle_rounds,
                    "radius2_failure_clauses": [serialized_clause(clause)
                                                for clause in radius2_clauses],
                    "first_corona_failure_clauses": [serialized_clause(clause)
                                                     for clause in outer_clauses],
                    "radius2_patch": middle["radius2_patch"],
                    "added_patch": middle["added_patch"],
                    "replay": middle["replay"],
                    "milliseconds": round((time.monotonic() - started) * 1000),
                    "seed_milliseconds": seed_milliseconds,
                    "cumulative_milliseconds": seed_milliseconds + round(
                        (time.monotonic() - started) * 1000),
                },
            }
        if middle["result"] != "exhausted":
            stopped_by = middle["stopped_by"]
            break
        core_keys = [key(selected_first[index]) for index in middle["outer_core"]]
        signature = clause_signature(core_keys)
        if signature not in outer_signatures:
            outer_signatures.add(signature)
            outer_clauses.append(signature)
        indices = [first_indices[index] for index in middle["outer_core"]]
        outer.add(Or([Not(outer_variables[index]) for index in indices])
                  if indices else BoolVal(False))
    else:
        stopped_by = "outer_round_limit"
    return {
        **record,
        "radius3_gcts_classification": "unresolved",
        "radius3_gcts": {
            "outer_exhausted": False,
            "outer_rounds": len(outer_clauses),
            "continuation_outer_rounds": max(0, len(outer_clauses) - len(
                decoded_clauses(seed_receipt.get("first_corona_failure_clauses", [])))),
            "middle_rounds": seed_middle_rounds + total_middle_rounds,
            "continuation_middle_rounds": total_middle_rounds,
            "radius2_failure_clauses": [serialized_clause(clause)
                                        for clause in radius2_clauses],
            "first_corona_failure_clauses": [serialized_clause(clause)
                                             for clause in outer_clauses],
            "stopped_by": stopped_by,
            "milliseconds": round((time.monotonic() - started) * 1000),
            "seed_milliseconds": seed_milliseconds,
            "cumulative_milliseconds": seed_milliseconds + round(
                (time.monotonic() - started) * 1000),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--outer-rounds", type=int, default=32)
    parser.add_argument("--middle-rounds", type=int, default=128)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--backend", choices=("z3", "qffd"), default="qffd")
    parser.add_argument("--inner-node-limit", type=int, default=500000)
    parser.add_argument("--resume")
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines()
               if line.strip()]
    if requested:
        records = [record for record in records if record["id"] in requested]
    seeds = {}
    if args.resume:
        seeds = {
            item["id"]: item
            for item in (json.loads(line) for line in Path(args.resume).read_text().splitlines()
                         if line.strip())
        }
    output = Path(args.output)
    output.write_text("")
    counts: dict[str, int] = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.outer_rounds, args.middle_rounds,
                            args.timeout_ms, args.backend, seeds.get(record["id"]),
                            args.inner_node_limit)
            classification = result["radius3_gcts_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
