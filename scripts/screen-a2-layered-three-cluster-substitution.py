#!/usr/bin/env python3
"""Exact scalar-2 mixed substitution screen for connected three-copy A2 metatiles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, PbEq, SolverFor, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TWO = load("a2_two_cluster", "screen-a2-layered-two-cluster-substitution.py")
SUBSTITUTION = TWO.SUBSTITUTION


def enumerate_three_copy_metatiles(record):
    two_copy = TWO.enumerate_two_copy_metatiles(record)["metatiles"]
    tile_orientations = SUBSTITUTION.oriented_cells(record["cells"])
    representatives = {}
    raw_extensions = 0
    for cluster in two_copy:
        occupied = {SUBSTITUTION.cell_key(cell) for cell in cluster["cells"]}
        for neighbor in TWO.adjacent_atomic_cells(cluster["cells"]):
            neighbor_key = SUBSTITUTION.cell_key(neighbor)
            for orientation_index, orientation in enumerate(tile_orientations):
                for own_cell in orientation["cells"]:
                    own_key = SUBSTITUTION.cell_key(own_cell)
                    if own_key[3] != neighbor_key[3]:
                        continue
                    delta = tuple(neighbor_key[axis] - own_key[axis] for axis in range(3))
                    third = TWO.translated_cells(orientation["cells"], delta)
                    third_keys = {SUBSTITUTION.cell_key(cell) for cell in third}
                    if occupied.intersection(third_keys):
                        continue
                    raw_extensions += 1
                    union = [*cluster["cells"], *third]
                    key = TWO.canonical_key(union)
                    if key in representatives:
                        continue
                    representatives[key] = {
                        "cells": union,
                        "canonical_key": [list(cell) for cell in key],
                        "third_orientation_index": orientation_index,
                        "third_translation": list(delta),
                    }
    ordered_keys = sorted(representatives)
    ordered = [representatives[key] for key in ordered_keys]
    digest = hashlib.sha256(json.dumps(
        [item["canonical_key"] for item in ordered], separators=(",", ":")
    ).encode()).hexdigest()
    return {
        "two_copy_parent_types": len(two_copy),
        "raw_three_copy_extensions": raw_extensions,
        "symmetry_distinct_metatiles": len(ordered),
        "canonical_sha256": digest,
        "metatiles": ordered,
    }


def placement_graph(target, tile_orientations):
    placements = SUBSTITUTION.candidate_placements(target, tile_orientations)
    cell_sets = [set(placement["cells"]) for placement in placements]
    face_sets = []
    by_cell = {cell: [] for cell in target}
    for index, cells in enumerate(cell_sets):
        faces = set()
        for q, r, k, kind in cells:
            faces.update(TWO.cell_faces({"q": q, "r": r, "k": k, "kind": kind}))
            by_cell[(q, r, k, kind)].append(index)
        face_sets.append(faces)
    adjacency = [set() for _ in placements]
    for left in range(len(placements)):
        for right in range(left + 1, len(placements)):
            if (
                cell_sets[left].isdisjoint(cell_sets[right])
                and face_sets[left].intersection(face_sets[right])
            ):
                adjacency[left].add(right)
                adjacency[right].add(left)
    return {
        "placements": placements,
        "cell_sets": cell_sets,
        "adjacency": adjacency,
        "by_cell": by_cell,
    }


def connected_triple_covering(graph, target_cell):
    cell_sets = graph["cell_sets"]
    adjacency = graph["adjacency"]
    checks = 0
    for first in graph["by_cell"].get(target_cell, []):
        for second in adjacency[first]:
            pair_cells = cell_sets[first].union(cell_sets[second])
            for third in adjacency[first].union(adjacency[second]):
                checks += 1
                if third in (first, second):
                    continue
                if pair_cells.isdisjoint(cell_sets[third]):
                    return (first, second, third), checks
    return None, checks


def first_uncovered_by_three_cluster(target, graph):
    checks = 0
    for target_cell in sorted(target):
        triple, cell_checks = connected_triple_covering(graph, target_cell)
        checks += cell_checks
        if triple is None:
            return target_cell, checks
    return None, checks


def replay_local_obstruction(target, tile_orientations, target_cell):
    graph = placement_graph(target, tile_orientations)
    triple, checks = connected_triple_covering(graph, target_cell)
    return {
        "verified": triple is None,
        "method": "independent_contained_monotile_placement_graph",
        "uncovered_cell": list(target_cell),
        "monotile_placements": len(graph["placements"]),
        "connected_triple_checks": checks,
        "unexpected_triple": list(triple) if triple is not None else None,
    }


def all_connected_triple_placements(graph):
    unions = {}
    cell_sets = graph["cell_sets"]
    adjacency = graph["adjacency"]
    for first in range(len(cell_sets)):
        for second in adjacency[first]:
            if second <= first:
                continue
            pair_cells = cell_sets[first].union(cell_sets[second])
            for third in adjacency[first].union(adjacency[second]):
                if third in (first, second) or not pair_cells.isdisjoint(cell_sets[third]):
                    continue
                indices = tuple(sorted((first, second, third)))
                cells = frozenset(pair_cells.union(cell_sets[third]))
                unions.setdefault(cells, indices)
    return [
        {"cells": cells, "component_placement_indices": list(indices)}
        for cells, indices in unions.items()
    ]


def identify_metatile_placement(metatile_cells, placed_cells):
    placed = set(placed_cells)
    for orientation_index, orientation in enumerate(
        SUBSTITUTION.oriented_cells(metatile_cells)
    ):
        own = [SUBSTITUTION.cell_key(cell) for cell in orientation["cells"]]
        for placed_anchor in placed:
            for own_anchor in own:
                if placed_anchor[3] != own_anchor[3]:
                    continue
                delta = tuple(placed_anchor[axis] - own_anchor[axis] for axis in range(3))
                translated = {
                    (
                        cell[0] + delta[0], cell[1] + delta[1],
                        cell[2] + delta[2], cell[3],
                    )
                    for cell in own
                }
                if translated == placed:
                    return {
                        "orientation_index": orientation_index,
                        "translation": list(delta),
                    }
    return None


def replay_unsat_with_qffd(target, placements, timeout_ms):
    variables = [Bool(f"three_cluster_replay_{index}") for index in range(len(placements))]
    incidence = {cell: [] for cell in target}
    for index, placement in enumerate(placements):
        for cell in placement["cells"]:
            incidence[cell].append(index)
    solver = SolverFor("QF_FD")
    solver.set(timeout=timeout_ms)
    for cell in sorted(target):
        solver.add(PbEq([(variables[index], 1) for index in incidence[cell]], 1))
    result = solver.check()
    return {
        "verified": result == unsat,
        "method": "independent_z3_qf_fd_atomic_exact_cover",
        "result": "unsat" if result == unsat else ("sat" if result == sat else "unknown"),
        "variables": len(variables),
        "constraints": len(target),
        "timeout_ms": timeout_ms,
    }


def replay_unsat_with_independent_algorithm_x(target, placements, timeout_ms):
    ordered_target = sorted(target, reverse=True)
    target_index = {cell: index for index, cell in enumerate(ordered_target)}
    masks = [
        sum(1 << target_index[cell] for cell in placement["cells"])
        for placement in placements
    ]
    by_cell = [[] for _ in ordered_target]
    for placement_index, mask in enumerate(masks):
        bits = mask
        while bits:
            lowest = bits & -bits
            by_cell[lowest.bit_length() - 1].append(placement_index)
            bits ^= lowest
    full = (1 << len(ordered_target)) - 1
    deadline = time.monotonic() + timeout_ms / 1000
    failed = set()
    nodes = 0
    timed_out = False

    def visit(covered):
        nonlocal nodes, timed_out
        nodes += 1
        if covered == full:
            return True
        if time.monotonic() >= deadline:
            timed_out = True
            return False
        if covered in failed:
            return False
        choices = []
        remaining = full ^ covered
        while remaining:
            lowest = remaining & -remaining
            cell_index = lowest.bit_length() - 1
            legal = [
                index for index in by_cell[cell_index]
                if masks[index] & covered == 0
            ]
            if not legal:
                failed.add(covered)
                return False
            choices.append((len(legal), -cell_index, legal))
            remaining ^= lowest
        _, _, legal = min(choices)
        for placement_index in reversed(legal):
            if visit(covered | masks[placement_index]):
                return True
            if timed_out:
                return False
        failed.add(covered)
        return False

    satisfiable = visit(0)
    result = "unknown" if timed_out else ("sat" if satisfiable else "unsat")
    return {
        "verified": result == "unsat",
        "method": "independent_reverse_order_algorithm_x",
        "result": result,
        "placements": len(placements),
        "constraints": len(target),
        "nodes": nodes,
        "failed_states": len(failed),
        "timeout_ms": timeout_ms,
    }


def screen_candidate(record, timeout_ms=30000, replay_timeout_ms=300000, progress_every=250):
    started = time.monotonic()
    enumerated = enumerate_three_copy_metatiles(record)
    metatiles = enumerated["metatiles"]
    canonical_index = {
        tuple(tuple(cell) for cell in metatile["canonical_key"]): index
        for index, metatile in enumerate(metatiles)
    }
    tile_orientations = SUBSTITUTION.oriented_cells(record["cells"])
    parent_results = []
    for parent_index, parent in enumerate(metatiles):
        target = SUBSTITUTION.scaled_cells(parent["cells"], 2)
        graph = placement_graph(target, tile_orientations)
        uncovered, checks = first_uncovered_by_three_cluster(target, graph)
        common = {
            "parent_index": parent_index,
            "target_cells": len(target),
            "monotile_placements": len(graph["placements"]),
            "local_connected_triple_checks": checks,
        }
        if uncovered is not None:
            replay = replay_local_obstruction(target, tile_orientations, uncovered)
            if not replay["verified"]:
                raise RuntimeError(f"three-cluster local replay failed: {replay}")
            parent_results.append({
                **common,
                "classification": "local_obstruction",
                "local_obstruction_replay": replay,
            })
        else:
            placements = all_connected_triple_placements(graph)
            if progress_every:
                print(
                    f"  {record['id']} parent {parent_index} exact fallback "
                    f"({len(placements)} cluster placements)",
                    flush=True,
                )
            solved = SUBSTITUTION.exact_cover(target, placements, timeout_ms)
            exact_common = {
                **common,
                "three_cluster_placements": len(placements),
                "nodes": solved["nodes"],
                "failed_states": solved["failed_states"],
            }
            if solved["result"] == "sat":
                replay = SUBSTITUTION.replay(target, placements, solved["solution"], 8)
                if not replay["verified"]:
                    raise RuntimeError(f"three-cluster substitution replay failed: {replay}")
                rule = []
                for placement_index in solved["solution"]:
                    placement = placements[placement_index]
                    child_cells = [
                        {"q": q, "r": r, "k": k, "kind": kind}
                        for q, r, k, kind in placement["cells"]
                    ]
                    child_key = TWO.canonical_key(child_cells)
                    child_index = canonical_index.get(child_key)
                    if child_index is None:
                        raise RuntimeError("connected child cluster missing from complete alphabet")
                    pose = identify_metatile_placement(
                        metatiles[child_index]["cells"], placement["cells"]
                    )
                    if pose is None:
                        raise RuntimeError("child metatile pose could not be replayed")
                    rule.append({
                        "type_index": child_index,
                        **pose,
                        "component_placement_indices": placement["component_placement_indices"],
                    })
                parent_results.append({
                    **exact_common,
                    "classification": "mixed_metatile_rule",
                    "rule": rule,
                    "replay": replay,
                })
            elif solved["result"] == "unsat":
                algorithm_x_replay = replay_unsat_with_independent_algorithm_x(
                    target, placements, timeout_ms
                )
                replay = (
                    algorithm_x_replay if algorithm_x_replay["verified"]
                    else replay_unsat_with_qffd(target, placements, replay_timeout_ms)
                )
                parent_results.append({
                    **exact_common,
                    "classification": "exact_unsat" if replay["verified"] else "unresolved",
                    "primary_exact_result": "unsat",
                    "algorithm_x_replay": algorithm_x_replay,
                    "exact_unsat_replay": replay,
                    **({} if replay["verified"] else {"stopped_by": "independent_replay_timeout"}),
                })
            else:
                parent_results.append({
                    **exact_common,
                    "classification": "unresolved",
                    "stopped_by": "time_limit",
                })
        if progress_every and (parent_index + 1) % progress_every == 0:
            print(
                f"  {record['id']} parents {parent_index + 1}/{len(metatiles)}",
                flush=True,
            )

    rules = {
        result["parent_index"]: result
        for result in parent_results
        if result["classification"] == "mixed_metatile_rule"
    }
    closed_alphabet = None
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
                child_index = child["type_index"]
                if child_index not in closure:
                    closure.add(child_index)
                    frontier.append(child_index)
        if valid and (closed_alphabet is None or len(closure) < len(closed_alphabet)):
            closed_alphabet = sorted(closure)

    unknowns = sum(result["classification"] == "unresolved" for result in parent_results)
    if closed_alphabet is not None:
        classification = "three_copy_metatile_substitution_system"
        certified = True
    elif not rules and not unknowns:
        classification = "no_three_copy_metatile_scalar2_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    return {
        "id": record["id"],
        "cells": record["cells"],
        "classification": classification,
        "three_copy_metatile_screen": {
            "certified": certified,
            "inflation": "scalar_2",
            "family": "all_face_connected_three_copy_metatiles_modulo_proper_a2_isometry_and_translation",
            "two_copy_parent_types": enumerated["two_copy_parent_types"],
            "raw_three_copy_extensions": enumerated["raw_three_copy_extensions"],
            "symmetry_distinct_metatiles": enumerated["symmetry_distinct_metatiles"],
            "canonical_sha256": enumerated["canonical_sha256"],
            "closed_alphabet": closed_alphabet,
            "parent_counts": {
                name: sum(result["classification"] == name for result in parent_results)
                for name in ("local_obstruction", "exact_unsat", "mixed_metatile_rule", "unresolved")
            },
            "milliseconds": round((time.monotonic() - started) * 1000),
            "parent_results": parent_results,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--replay-timeout-ms", type=int, default=300000)
    parser.add_argument("--progress-every", type=int, default=250)
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = [
        json.loads(line) for line in Path(args.input).read_text().splitlines()
        if line.strip()
    ]
    if requested:
        records = [record for record in records if record["id"] in requested]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            screened = screen_candidate(
                record, args.timeout_ms, args.replay_timeout_ms, args.progress_every
            )
            classification = screened["classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(screened, separators=(",", ":")) + "\n")
            stream.flush()
            types = screened["three_copy_metatile_screen"]["symmetry_distinct_metatiles"]
            print(f"{index}/{len(records)} {record['id']} {classification} ({types} types)", flush=True)
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
