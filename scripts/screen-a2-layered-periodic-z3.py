#!/usr/bin/env python3
"""Exact periodic-quotient screen for A2 layered lattice functions.

The web search grows a boundary patch before looking for periods.  This tool
instead solves the finite weighted quotient directly: for each HNF sublattice,
one Boolean variable represents each oriented translate, every quotient point
must receive exactly 48 solid-angle units, and the selected copy count is
fixed.  Positive certificates are replayed independently with Cramer's-rule
quotient coordinates before they are written.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import time
from pathlib import Path

from z3 import Bool, If, Solver, Sum, is_true, sat, unsat


PERMUTATIONS = tuple(itertools.permutations(range(3)))


def permutation_parity(permutation: tuple[int, int, int]) -> int:
    inversions = sum(
        permutation[left] > permutation[right]
        for left in range(3)
        for right in range(left + 1, 3)
    )
    return -1 if inversions % 2 else 1


A2_LAYER_ISOMETRIES = tuple(
    (sign, permutation)
    for sign in (1, -1)
    for permutation in PERMUTATIONS
    if sign * permutation_parity(permutation) == 1
)


def cell_vertices(cell: dict) -> list[tuple[int, int, int]]:
    q, r, k, kind = cell["q"], cell["r"], cell["k"], cell["kind"]
    axial = (
        ((q, r), (q + 1, r), (q, r + 1))
        if kind == "u"
        else ((q + 1, r + 1), (q, r + 1), (q + 1, r))
    )
    base = [(x + k, y + k, -x - y + k) for x, y in axial]
    return base + [tuple(coordinate + 1 for coordinate in point) for point in base]


def tile_occupancy(cells: list[dict]) -> dict[tuple[int, int, int], int]:
    occupancy: dict[tuple[int, int, int], int] = {}
    for cell in cells:
        for point in cell_vertices(cell):
            occupancy[point] = occupancy.get(point, 0) + 4
    if any(weight <= 0 or weight > 48 for weight in occupancy.values()):
        raise ValueError("invalid A2 layered solid-angle occupancy")
    return occupancy


def orientations(occupancy: dict) -> list[dict]:
    result = []
    seen = set()
    for sign, permutation in A2_LAYER_ISOMETRIES:
        transformed = {
            tuple(sign * point[permutation[axis]] for axis in range(3)): weight
            for point, weight in occupancy.items()
        }
        key = tuple(sorted(transformed.items()))
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "occupancy": transformed,
            "sign": sign,
            "permutation": permutation,
        })
    return result


def hnf_candidates(determinant: int):
    candidates = []
    for a in range(1, determinant + 1):
        if determinant % a:
            continue
        for d in range(1, determinant // a + 1):
            if determinant % (a * d):
                continue
            f = determinant // (a * d)
            for b in range(a):
                for c in range(a):
                    for e in range(d):
                        candidates.append((a, b, c, d, e, f))
    return sorted(candidates, key=lambda hnf: (
        max(hnf[0], hnf[3], hnf[5]) - min(hnf[0], hnf[3], hnf[5]),
        hnf[1] + hnf[2] + hnf[4],
        hnf,
    ))


def period_vectors(hnf: tuple[int, int, int, int, int, int]):
    a, b, c, d, e, f = hnf
    return ((a, 0, 0), (b, d, 0), (c, e, f))


def reduce_hnf(point: tuple[int, int, int], hnf) -> tuple[int, int, int]:
    x, y, z = point
    a, b, c, d, e, f = hnf
    quotient = z // f
    x, y, z = x - quotient * c, y - quotient * e, z - quotient * f
    quotient = y // d
    x, y = x - quotient * b, y - quotient * d
    quotient = x // a
    x -= quotient * a
    return x % a, y % d, z % f


def quotient_index(point, hnf) -> int:
    x, y, z = reduce_hnf(point, hnf)
    return x + hnf[0] * (y + hnf[3] * z)


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def replay_certificate(tile_orientations, certificate: dict) -> dict:
    basis = tuple(tuple(vector) for vector in certificate["period_vectors"])
    determinant = abs(dot(basis[0], cross(basis[1], basis[2])))
    if determinant != certificate["determinant"]:
        return {"verified": False, "reason": "determinant_mismatch"}
    numerators = (
        cross(basis[1], basis[2]),
        cross(basis[2], basis[0]),
        cross(basis[0], basis[1]),
    )
    weights: dict[tuple[int, int, int], int] = {}
    for placement in certificate["placements"]:
        orientation_index = placement["orientation_index"]
        if orientation_index < 0 or orientation_index >= len(tile_orientations):
            return {"verified": False, "reason": "unknown_orientation"}
        translation = tuple(placement["translation"])
        for point, weight in tile_orientations[orientation_index]["occupancy"].items():
            translated = tuple(point[axis] + translation[axis] for axis in range(3))
            signature = tuple(dot(translated, numerator) % determinant for numerator in numerators)
            weights[signature] = weights.get(signature, 0) + weight
    if len(weights) != determinant:
        return {"verified": False, "reason": "quotient_not_full", "classes": len(weights)}
    if any(weight != 48 for weight in weights.values()):
        return {"verified": False, "reason": "quotient_weight_mismatch"}
    return {
        "verified": True,
        "method": "independent_cramers_rule_weighted_quotient",
        "determinant": determinant,
        "classes": len(weights),
    }


def screen_candidate(record: dict, args) -> dict:
    started = time.monotonic()
    occupancy = tile_occupancy(record["cells"])
    tile_orientations = orientations(occupancy)
    weight = sum(occupancy.values())
    hnf_visited = 0
    solver_unknown = 0
    exhausted_by_copies: dict[str, int] = {}
    for copies in range(args.min_copies, args.max_copies + 1):
        numerator = weight * copies
        if numerator % 48:
            continue
        determinant = numerator // 48
        candidates = hnf_candidates(determinant)
        copy_unknown = 0
        for hnf_index, hnf in enumerate(candidates):
            hnf_visited += 1
            placements = []
            for orientation_index, orientation in enumerate(tile_orientations):
                for x in range(hnf[0]):
                    for y in range(hnf[3]):
                        for z in range(hnf[5]):
                            vector = [0] * determinant
                            for point, point_weight in orientation["occupancy"].items():
                                translated = (point[0] + x, point[1] + y, point[2] + z)
                                vector[quotient_index(translated, hnf)] += point_weight
                            placements.append({
                                "orientation_index": orientation_index,
                                "translation": (x, y, z),
                                "weights": vector,
                            })

            # Translation and global proper-layer rotation allow an arbitrary
            # tiling copy to be fixed as the identity placement at the origin.
            # The one- and two-copy cases are complete vector/complement tests;
            # only larger motifs need a pseudo-Boolean solver.
            chosen_indices = None
            if copies == 1:
                chosen_indices = [0] if all(weight == 48 for weight in placements[0]["weights"]) else None
                result = sat if chosen_indices else unsat
                model = None
                variables = []
            elif copies == 2:
                complement = tuple(48 - weight for weight in placements[0]["weights"])
                match = next((
                    index for index, placement in enumerate(placements)
                    if index != 0 and tuple(placement["weights"]) == complement
                ), None)
                chosen_indices = [0, match] if match is not None else None
                result = sat if chosen_indices else unsat
                model = None
                variables = []
            elif copies in (3, 4):
                complement = tuple(48 - weight for weight in placements[0]["weights"])
                eligible = [
                    index for index, placement in enumerate(placements)
                    if index != 0 and all(
                        weight <= complement[residue]
                        for residue, weight in enumerate(placement["weights"])
                    )
                ]
                pair_sums: dict[tuple[int, ...], list[tuple[int, int]]] = {}
                for left_offset, left in enumerate(eligible):
                    left_weights = placements[left]["weights"]
                    for right in eligible[left_offset + 1:]:
                        summed = tuple(
                            left_weights[residue] + placements[right]["weights"][residue]
                            for residue in range(determinant)
                        )
                        if any(summed[residue] > complement[residue] for residue in range(determinant)):
                            continue
                        pair_sums.setdefault(summed, []).append((left, right))
                if copies == 3:
                    pair = next(iter(pair_sums.get(complement, [])), None)
                    chosen_indices = [0, *pair] if pair else None
                else:
                    chosen_indices = None
                    for third in eligible:
                        target = tuple(
                            complement[residue] - placements[third]["weights"][residue]
                            for residue in range(determinant)
                        )
                        pair = next((
                            pair for pair in pair_sums.get(target, [])
                            if third not in pair
                        ), None)
                        if pair:
                            chosen_indices = [0, pair[0], pair[1], third]
                            break
                result = sat if chosen_indices else unsat
                model = None
                variables = []
            else:
                variables = [Bool(f"p_{copies}_{hnf_index}_{index}") for index in range(len(placements))]
                solver = Solver()
                solver.set(timeout=args.hnf_timeout_ms)
                solver.add(variables[0])
                solver.add(Sum([If(variable, 1, 0) for variable in variables]) == copies)
                for residue in range(determinant):
                    solver.add(Sum([
                        If(variable, placement["weights"][residue], 0)
                        for variable, placement in zip(variables, placements)
                    ]) == 48)
                result = solver.check()
                model = solver.model() if result == sat else None
            if result == sat:
                if chosen_indices is None:
                    chosen_indices = [
                        index for index, variable in enumerate(variables)
                        if is_true(model.eval(variable))
                    ]
                chosen = [
                    {
                        "orientation_index": placement["orientation_index"],
                        "translation": list(placement["translation"]),
                    }
                    for index, placement in enumerate(placements)
                    if index in chosen_indices
                ]
                certificate = {
                    "kind": "weighted_periodic_hnf_quotient",
                    "certified": True,
                    "can_tile": True,
                    "model": "a2_layered_lattice_function",
                    "copies": copies,
                    "determinant": determinant,
                    "period_vectors": [list(vector) for vector in period_vectors(hnf)],
                    "placements": chosen,
                    "hnf_index": hnf_index,
                }
                replay = replay_certificate(tile_orientations, certificate)
                if not replay["verified"]:
                    raise RuntimeError(f"certificate replay failed: {replay}")
                return {
                    **record,
                    "classification": "periodic",
                    "periodic_z3": {
                        "certificate": certificate,
                        "replay": replay,
                        "hnf_visited": hnf_visited,
                        "solver_unknown": solver_unknown,
                        "exhausted_by_copies": exhausted_by_copies,
                        "milliseconds": round((time.monotonic() - started) * 1000),
                    },
                }
            if result != unsat:
                solver_unknown += 1
                copy_unknown += 1
            if args.candidate_time_ms and (time.monotonic() - started) * 1000 >= args.candidate_time_ms:
                return {
                    **record,
                    "classification": "unresolved",
                    "periodic_z3": {
                        "stopped_by": "candidate_time_limit",
                        "active_copies": copies,
                        "hnf_visited": hnf_visited,
                        "solver_unknown": solver_unknown,
                        "exhausted_by_copies": exhausted_by_copies,
                        "milliseconds": round((time.monotonic() - started) * 1000),
                    },
                }
        if copy_unknown == 0:
            exhausted_by_copies[str(copies)] = len(candidates)
    return {
        **record,
        "classification": "unresolved",
        "periodic_z3": {
            "stopped_by": None,
            "hnf_visited": hnf_visited,
            "solver_unknown": solver_unknown,
            "exhausted_by_copies": exhausted_by_copies,
            "milliseconds": round((time.monotonic() - started) * 1000),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-copies", type=int, default=1)
    parser.add_argument("--max-copies", type=int, default=6)
    parser.add_argument("--hnf-timeout-ms", type=int, default=5000)
    parser.add_argument("--candidate-time-ms", type=int, default=0)
    parser.add_argument("--only-unresolved", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.min_copies < 1 or args.max_copies < args.min_copies:
        parser.error("invalid copy range")

    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    if args.only_unresolved:
        records = [record for record in records if record.get("classification") == "unresolved"]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    counts = {"periodic": 0, "unresolved": 0}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            screened = screen_candidate(record, args)
            counts[screened["classification"]] += 1
            stream.write(json.dumps(screened, separators=(",", ":")) + "\n")
            stream.flush()
            certificate = screened["periodic_z3"].get("certificate")
            suffix = f" {certificate['copies']}-copy det={certificate['determinant']}" if certificate else ""
            print(f"{index}/{len(records)} {record['id']} {screened['classification']}{suffix}", flush=True)
    print(json.dumps({"records": len(records), **counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
