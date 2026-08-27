#!/usr/bin/env python3
"""Exact scalar mixed-substitution screen for connected three-copy A2 metatiles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from z3 import Bool, Not, Or, PbEq, SolverFor, is_true, sat, unsat


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
    cell_index = {cell: index for index, cell in enumerate(sorted(target))}
    cell_masks = [
        sum(1 << cell_index[cell] for cell in cells)
        for cells in cell_sets
    ]
    by_cell = {cell: [] for cell in target}
    for index, cells in enumerate(cell_sets):
        for q, r, k, kind in cells:
            by_cell[(q, r, k, kind)].append(index)
    adjacency = [set() for _ in placements]
    candidate_pairs = set()
    for left, cells in enumerate(cell_sets):
        boundary = set()
        for q, r, k, kind in cells:
            if kind == "u":
                neighbors = (
                    (q, r, k - 1, "u"), (q, r, k + 1, "u"),
                    (q, r, k, "d"), (q - 1, r, k, "d"),
                    (q, r - 1, k, "d"),
                )
            else:
                neighbors = (
                    (q, r, k - 1, "d"), (q, r, k + 1, "d"),
                    (q, r, k, "u"), (q + 1, r, k, "u"),
                    (q, r + 1, k, "u"),
                )
            boundary.update(neighbor for neighbor in neighbors if neighbor not in cells)
        for neighbor in boundary:
            for right in by_cell.get(neighbor, []):
                if right <= left:
                    continue
                candidate_pairs.add((left, right))
                if cell_masks[left] & cell_masks[right] == 0:
                    adjacency[left].add(right)
                    adjacency[right].add(left)
    graph_sha256 = hashlib.sha256(json.dumps({
        "placements": [
            [placement["orientation_index"], placement["translation"]]
            for placement in placements
        ],
        "adjacency": [sorted(neighbors) for neighbors in adjacency],
    }, separators=(",", ":")).encode()).hexdigest()
    return {
        "placements": placements,
        "cell_sets": cell_sets,
        "cell_index": cell_index,
        "cell_masks": cell_masks,
        "adjacency": adjacency,
        "by_cell": by_cell,
        "adjacency_candidate_pairs": len(candidate_pairs),
        "sha256": graph_sha256,
    }


def connected_triple_covering(graph, target_cell):
    cell_masks = graph["cell_masks"]
    adjacency = graph["adjacency"]
    checks = 0
    for first in graph["by_cell"].get(target_cell, []):
        for second in adjacency[first]:
            pair_mask = cell_masks[first] | cell_masks[second]
            for third in adjacency[first].union(adjacency[second]):
                checks += 1
                if third in (first, second):
                    continue
                if pair_mask & cell_masks[third] == 0:
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


def replay_local_obstruction(target, tile_orientations, target_cell, graph=None):
    reused_graph = graph is not None
    graph = graph or placement_graph(target, tile_orientations)
    triple, checks = connected_triple_covering(graph, target_cell)
    return {
        "verified": triple is None,
        "method": (
            "hashed_exhaustive_contained_monotile_graph_replay"
            if reused_graph else "independent_contained_monotile_placement_graph"
        ),
        "uncovered_cell": list(target_cell),
        "monotile_placements": len(graph["placements"]),
        "connected_triple_checks": checks,
        "unexpected_triple": list(triple) if triple is not None else None,
        "placement_graph_sha256": graph["sha256"],
        "adjacency_candidate_pairs": graph["adjacency_candidate_pairs"],
    }


def all_connected_triple_placements(graph):
    unions = {}
    cell_sets = graph["cell_sets"]
    adjacency = graph["adjacency"]
    cell_masks = graph["cell_masks"]
    for first in range(len(cell_sets)):
        for second in adjacency[first]:
            if second <= first:
                continue
            pair_mask = cell_masks[first] | cell_masks[second]
            for third in adjacency[first].union(adjacency[second]):
                if third in (first, second) or pair_mask & cell_masks[third]:
                    continue
                indices = tuple(sorted((first, second, third)))
                cells = frozenset(
                    cell_sets[first].union(cell_sets[second], cell_sets[third])
                )
                unions.setdefault(cells, indices)
    return [
        {"cells": cells, "component_placement_indices": list(indices)}
        for cells, indices in unions.items()
    ]


def partition_selected_placements(graph, selected):
    selected_set = set(selected)
    adjacency = graph["adjacency"]
    triples = set()
    for first in selected:
        for second in adjacency[first].intersection(selected_set):
            if second <= first:
                continue
            for third in (
                adjacency[first].union(adjacency[second]).intersection(selected_set)
            ):
                if third in (first, second):
                    continue
                triples.add(tuple(sorted((first, second, third))))
    by_placement = {index: [] for index in selected}
    for triple in sorted(triples):
        for index in triple:
            by_placement[index].append(triple)
    failed = set()

    def visit(remaining):
        if not remaining:
            return []
        signature = frozenset(remaining)
        if signature in failed:
            return None
        choices = [
            (sum(all(member in remaining for member in triple) for triple in by_placement[index]), index)
            for index in remaining
        ]
        count, pivot = min(choices)
        if count == 0:
            failed.add(signature)
            return None
        for triple in by_placement[pivot]:
            if not all(member in remaining for member in triple):
                continue
            suffix = visit(remaining.difference(triple))
            if suffix is not None:
                return [triple, *suffix]
        failed.add(signature)
        return None

    solution = visit(set(selected))
    return {
        "result": "sat" if solution is not None else "unsat",
        "solution": solution,
        "connected_triples": len(triples),
        "failed_states": len(failed),
    }


def compact_three_cluster_exact_cover(target, graph, timeout_ms, max_models=256):
    started = time.monotonic()
    variables = [Bool(f"compact_monotile_{index}") for index in range(len(graph["placements"]))]
    incidence = {cell: [] for cell in target}
    for index, placement in enumerate(graph["placements"]):
        for cell in placement["cells"]:
            incidence[cell].append(index)
    solver = SolverFor("QF_FD")
    for cell in sorted(target):
        solver.add(PbEq([(variables[index], 1) for index in incidence[cell]], 1))
    rejected_models = 0
    partition_attempts = []
    while rejected_models < max_models:
        remaining_ms = timeout_ms - round((time.monotonic() - started) * 1000)
        if remaining_ms <= 0:
            return {
                "result": "unknown",
                "stopped_by": "time_limit",
                "monotile_placements": len(variables),
                "models_rejected": rejected_models,
                "partition_attempts": partition_attempts,
            }
        solver.set(timeout=remaining_ms)
        result = solver.check()
        if result == unsat:
            return {
                "result": "unsat",
                "monotile_placements": len(variables),
                "models_rejected": rejected_models,
                "partition_attempts": partition_attempts,
            }
        if result != sat:
            return {
                "result": "unknown",
                "stopped_by": "solver_timeout",
                "monotile_placements": len(variables),
                "models_rejected": rejected_models,
                "partition_attempts": partition_attempts,
            }
        model = solver.model()
        selected = [
            index for index, variable in enumerate(variables)
            if is_true(model.eval(variable))
        ]
        partition = partition_selected_placements(graph, selected)
        partition_attempts.append({
            "selected_monotiles": len(selected),
            "connected_triples": partition["connected_triples"],
            "failed_states": partition["failed_states"],
            "result": partition["result"],
        })
        if partition["result"] == "sat":
            return {
                "result": "sat",
                "monotile_placements": len(variables),
                "models_rejected": rejected_models,
                "selected": selected,
                "solution": partition["solution"],
                "partition_attempts": partition_attempts,
            }
        solver.add(Or([
            Not(variable) if index in selected else variable
            for index, variable in enumerate(variables)
        ]))
        rejected_models += 1
    return {
        "result": "unknown",
        "stopped_by": "model_limit",
        "monotile_placements": len(variables),
        "models_rejected": rejected_models,
        "partition_attempts": partition_attempts,
    }


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


def screen_candidate(
    record, timeout_ms=30000, replay_timeout_ms=300000, progress_every=250,
    scale=2, seed_report=None, checkpoint_every=0, checkpoint_callback=None,
):
    started = time.monotonic()
    enumerated = enumerate_three_copy_metatiles(record)
    metatiles = enumerated["metatiles"]
    canonical_index = {
        tuple(tuple(cell) for cell in metatile["canonical_key"]): index
        for index, metatile in enumerate(metatiles)
    }
    tile_orientations = SUBSTITUTION.oriented_cells(record["cells"])
    elapsed_base = 0
    parent_results = []
    if seed_report is not None:
        seed_screen = seed_report["three_copy_metatile_screen"]
        if seed_report["id"] != record["id"]:
            raise RuntimeError("checkpoint candidate id mismatch")
        if seed_screen.get("scale") != scale:
            raise RuntimeError("checkpoint inflation scale mismatch")
        if seed_screen["canonical_sha256"] != enumerated["canonical_sha256"]:
            raise RuntimeError("checkpoint metatile-family hash mismatch")
        if seed_screen["symmetry_distinct_metatiles"] != len(metatiles):
            raise RuntimeError("checkpoint metatile-family size mismatch")
        parent_results = list(seed_screen["parent_results"])
        if any(
            result["parent_index"] != index
            for index, result in enumerate(parent_results)
        ):
            raise RuntimeError("checkpoint parent results are not a consecutive prefix")
        elapsed_base = seed_screen.get("milliseconds", 0)

    def build_report(classification, certified, closed_alphabet):
        return {
            "id": record["id"],
            "cells": record["cells"],
            "classification": classification,
            "three_copy_metatile_screen": {
                "certified": certified,
                "inflation": f"scalar_{scale}",
                "scale": scale,
                "family": "all_face_connected_three_copy_metatiles_modulo_proper_a2_isometry_and_translation",
                "two_copy_parent_types": enumerated["two_copy_parent_types"],
                "raw_three_copy_extensions": enumerated["raw_three_copy_extensions"],
                "symmetry_distinct_metatiles": enumerated["symmetry_distinct_metatiles"],
                "canonical_sha256": enumerated["canonical_sha256"],
                "closed_alphabet": closed_alphabet,
                "parents_completed": len(parent_results),
                "parent_counts": {
                    name: sum(result["classification"] == name for result in parent_results)
                    for name in ("local_obstruction", "exact_unsat", "mixed_metatile_rule", "unresolved")
                },
                "milliseconds": elapsed_base + round((time.monotonic() - started) * 1000),
                "parent_results": parent_results,
            },
        }

    for parent_index in range(len(parent_results), len(metatiles)):
        parent = metatiles[parent_index]
        target = SUBSTITUTION.scaled_cells(parent["cells"], scale)
        graph = placement_graph(target, tile_orientations)
        uncovered, checks = first_uncovered_by_three_cluster(target, graph)
        common = {
            "parent_index": parent_index,
            "target_cells": len(target),
            "monotile_placements": len(graph["placements"]),
            "local_connected_triple_checks": checks,
        }
        if uncovered is not None:
            replay = replay_local_obstruction(
                target, tile_orientations, uncovered,
                graph if scale >= 3 else None,
            )
            if not replay["verified"]:
                raise RuntimeError(f"three-cluster local replay failed: {replay}")
            parent_results.append({
                **common,
                "classification": "local_obstruction",
                "local_obstruction_replay": replay,
            })
        else:
            compact = None
            if scale >= 3:
                compact = compact_three_cluster_exact_cover(
                    target, graph, timeout_ms
                )
                if compact["result"] == "sat":
                    placements = []
                    for triple in compact["solution"]:
                        cells = frozenset().union(*(
                            graph["cell_sets"][index] for index in triple
                        ))
                        placements.append({
                            "cells": cells,
                            "component_placement_indices": list(triple),
                        })
                    solved = {
                        "result": "sat",
                        "solution": list(range(len(placements))),
                        "nodes": sum(
                            attempt["failed_states"]
                            for attempt in compact["partition_attempts"]
                        ),
                        "failed_states": sum(
                            attempt["failed_states"]
                            for attempt in compact["partition_attempts"]
                        ),
                    }
                elif compact["result"] == "unsat":
                    placements = graph["placements"]
                    solved = {
                        "result": "unsat",
                        "solution": None,
                        "nodes": 0,
                        "failed_states": 0,
                    }
                else:
                    placements = graph["placements"]
                    solved = {
                        "result": "unknown",
                        "solution": None,
                        "nodes": 0,
                        "failed_states": 0,
                    }
            else:
                placements = all_connected_triple_placements(graph)
                solved = SUBSTITUTION.exact_cover(target, placements, timeout_ms)
            if progress_every:
                print(
                    f"  {record['id']} parent {parent_index} exact fallback "
                    f"({len(placements)} {'monotile' if compact and compact['result'] != 'sat' else 'cluster'} placements)",
                    flush=True,
                )
            exact_common = {
                **common,
                "exact_encoding": "compact_monotile_cover_partition_cegar" if compact else "explicit_connected_triples",
                "three_cluster_placements": len(placements) if compact is None or compact["result"] == "sat" else None,
                "compact_exact": compact,
                "nodes": solved["nodes"],
                "failed_states": solved["failed_states"],
            }
            if solved["result"] == "sat":
                replay = SUBSTITUTION.replay(
                    target, placements, solved["solution"], scale ** 3
                )
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
        if (
            checkpoint_callback is not None and checkpoint_every > 0
            and (
                (parent_index + 1) % checkpoint_every == 0
                or uncovered is None
            )
        ):
            checkpoint_callback(build_report("partial", False, None))

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
        classification = f"no_three_copy_metatile_scalar{scale}_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    return build_report(classification, certified, closed_alphabet)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--replay-timeout-ms", type=int, default=300000)
    parser.add_argument("--progress-every", type=int, default=250)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--checkpoint-every", type=int, default=50)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.scale < 2:
        parser.error("scale must be at least two")
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
            checkpoint = output.with_name(f"{output.name}.{record['id']}.checkpoint.ndjson")
            seed_report = None
            if args.resume and checkpoint.exists():
                seed_report = json.loads(checkpoint.read_text())

            def write_checkpoint(partial):
                checkpoint.write_text(json.dumps(partial, separators=(",", ":")) + "\n")

            screened = screen_candidate(
                record, args.timeout_ms, args.replay_timeout_ms, args.progress_every,
                args.scale, seed_report, args.checkpoint_every, write_checkpoint,
            )
            classification = screened["classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(screened, separators=(",", ":")) + "\n")
            stream.flush()
            types = screened["three_copy_metatile_screen"]["symmetry_distinct_metatiles"]
            print(f"{index}/{len(records)} {record['id']} {classification} ({types} types)", flush=True)
            if checkpoint.exists():
                checkpoint.unlink()
    print(json.dumps({"records": len(records), "counts": counts, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
