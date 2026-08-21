#!/usr/bin/env python3

import argparse
import itertools
import json
import time
from pathlib import Path

import z3


DIRECTIONS = (
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
)


def determinant(matrix):
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def proper_rotations():
    rotations = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            matrix = [[0, 0, 0] for _ in range(3)]
            for row in range(3):
                matrix[row][permutation[row]] = signs[row]
            if determinant(matrix) == 1:
                rotations.append(matrix)
    return rotations


def transform(cell, matrix):
    return tuple(sum(matrix[row][axis] * cell[axis] for axis in range(3)) for row in range(3))


def normalize(cells):
    minimum = tuple(min(cell[axis] for cell in cells) for axis in range(3))
    return tuple(sorted(tuple(cell[axis] - minimum[axis] for axis in range(3)) for cell in cells))


def orientations(voxels):
    unique = {}
    for matrix in proper_rotations():
        oriented = normalize(tuple(transform(cell, matrix) for cell in voxels))
        unique.setdefault(oriented, oriented)
    return tuple(unique.values())


def target_cells(root, layers):
    root_set = set(root)
    target = set()
    frontier = set(root)
    for _ in range(layers):
        next_frontier = set()
        for cell in frontier:
            for direction in DIRECTIONS:
                neighbor = tuple(cell[axis] + direction[axis] for axis in range(3))
                if neighbor in root_set or neighbor in target:
                    continue
                target.add(neighbor)
                next_frontier.add(neighbor)
        frontier = next_frontier
    return target


def enumerate_placements(root, layers):
    root_set = set(root)
    target = target_cells(root, layers)
    placement_set = set()
    for pivot in sorted(target):
        for orientation in orientations(root):
            for anchor in orientation:
                translation = tuple(pivot[axis] - anchor[axis] for axis in range(3))
                cells = tuple(sorted(tuple(cell[axis] + translation[axis] for axis in range(3)) for cell in orientation))
                if root_set.isdisjoint(cells):
                    placement_set.add(cells)
    return target, tuple(sorted(placement_set))


def parse_key(key):
    return tuple(tuple(int(value) for value in cell.split(",")) for cell in key.split(";") if cell)


def main():
    parser = argparse.ArgumentParser(description="Solve a finite polycube corona as an exact pseudo-Boolean cover in Z3.")
    parser.add_argument("--key", required=True)
    parser.add_argument("--layer", type=int, default=5)
    parser.add_argument("--timeout-ms", type=int, default=300_000)
    parser.add_argument("--backend", choices=("smt", "qffpbv", "pb2bv-sat"), default="smt")
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.layer < 1 or args.timeout_ms < 1:
        parser.error("layer and timeout must be positive")

    started = time.perf_counter()
    root = parse_key(args.key)
    target, placements = enumerate_placements(root, args.layer)
    by_cell = {}
    for index, placement in enumerate(placements):
        for cell in placement:
            by_cell.setdefault(cell, []).append(index)

    variables = [z3.Bool(f"p_{index}") for index in range(len(placements))]
    if args.backend == "qffpbv":
        solver = z3.Tactic("qffpbv").solver()
    elif args.backend == "pb2bv-sat":
        sat_tactic = z3.With(z3.Tactic("sat"), random_seed=args.random_seed)
        solver = z3.Then("simplify", "pb-preprocess", "pb2bv", sat_tactic).solver()
    else:
        solver = z3.Solver()
    solver.set(timeout=args.timeout_ms)
    for cell in sorted(target):
        indices = by_cell.get(cell, [])
        if not indices:
            solver.add(z3.BoolVal(False))
        else:
            solver.add(z3.PbEq([(variables[index], 1) for index in indices], 1))
    for cell, indices in sorted(by_cell.items()):
        if cell not in target and len(indices) > 1:
            solver.add(z3.PbLe([(variables[index], 1) for index in indices], 1))

    constraint_count = len(solver.assertions())
    status = solver.check()
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    selected = []
    if status == z3.sat:
        model = solver.model()
        selected = [placements[index] for index, variable in enumerate(variables) if z3.is_true(model.eval(variable))]
    report = {
        "kind": "polycube_corona_z3_exact_cover",
        "key": args.key,
        "layer": args.layer,
        "model": "proper cubic rotations; root fixed; primary target cells exactly once; secondary cells at most once",
        "backend": args.backend,
        "random_seed": args.random_seed,
        "target_cells": len(target),
        "placements_considered": len(placements),
        "variables": len(variables),
        "constraints": constraint_count,
        "timeout_ms": args.timeout_ms,
        "milliseconds": elapsed_ms,
        "classification": "verified_pending" if status == z3.sat else "certified_non_tiler" if status == z3.unsat else "incomplete",
        "z3_status": str(status),
        "reason_unknown": solver.reason_unknown() if status == z3.unknown else None,
        "corona": [{"cells": [list(cell) for cell in placement]} for placement in selected] if selected else None,
        "warning": None if status != z3.unknown else "A solver timeout is not a non-tiling or aperiodicity certificate.",
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "corona"}))


if __name__ == "__main__":
    main()
