#!/usr/bin/env python3
"""Resumable scalar-2 substitution screen for connected four-copy A2 metatiles."""

from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.util
import json
import sqlite3
import time
from pathlib import Path

from z3 import Bool, Not, Or, PbEq, SolverFor, is_true, sat, unsat


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FOUR = load("a2_four_cluster_enum", "enumerate-a2-layered-four-clusters.py")
THREE = FOUR.THREE
SUBSTITUTION = FOUR.SUBSTITUTION


def atomic_neighbors(cell):
    q, r, k, kind = cell
    if kind == "u":
        return (
            (q, r, k - 1, "u"), (q, r, k + 1, "u"),
            (q, r, k, "d"), (q - 1, r, k, "d"), (q, r - 1, k, "d"),
        )
    return (
        (q, r, k - 1, "d"), (q, r, k + 1, "d"),
        (q, r, k, "u"), (q + 1, r, k, "u"), (q, r + 1, k, "u"),
    )


def translated_orientation(orientation, target_cell, own_cell):
    delta = tuple(target_cell[axis] - own_cell[axis] for axis in range(3))
    return frozenset(
        (q + delta[0], r + delta[1], k + delta[2], kind)
        for q, r, k, kind in orientation
    )


@functools.lru_cache(maxsize=None)
def anchored_placements(target_cell, orientation_keys):
    placements = set()
    for orientation in orientation_keys:
        for own_cell in orientation:
            if own_cell[3] != target_cell[3]:
                continue
            placements.add(translated_orientation(orientation, target_cell, own_cell))
    return tuple(sorted(placements, key=lambda cells: tuple(sorted(cells))))


@functools.lru_cache(maxsize=None)
def inflated_atomic_cell(cell, scale=2):
    q, r, k, kind = cell
    return frozenset(SUBSTITUTION.scaled_cells([
        {"q": q, "r": r, "k": k, "kind": kind}
    ], scale))


def scaled_parent_cells(parent_cells, scale=2):
    return frozenset().union(*(
        inflated_atomic_cell(SUBSTITUTION.cell_key(cell), scale)
        for cell in parent_cells
    ))


@functools.lru_cache(maxsize=None)
def orientation_records(orientation_keys):
    return tuple({"cells": FOUR.cells_as_dicts(orientation)} for orientation in orientation_keys)


def placements_covering_cell(target, target_cell, orientation_keys, reverse=False):
    placements = [
        placed for placed in anchored_placements(target_cell, orientation_keys)
        if placed.issubset(target)
    ]
    return list(reversed(placements)) if reverse else placements


def adjacent_placements(target, occupied, orientation_keys, reverse=False):
    boundary = {
        neighbor
        for cell in occupied
        for neighbor in atomic_neighbors(cell)
        if neighbor not in occupied and neighbor in target
    }
    placements = set()
    boundary_order = sorted(boundary, reverse=reverse)
    for neighbor in boundary_order:
        for placed in anchored_placements(neighbor, orientation_keys):
            if placed.isdisjoint(occupied) and placed.issubset(target):
                placements.add(placed)
    return sorted(placements, key=lambda cells: tuple(sorted(cells)), reverse=reverse)


def connected_cluster_covering_cell(
    target, target_cell, orientation_keys, cluster_size=4, reverse=False,
):
    roots = placements_covering_cell(target, target_cell, orientation_keys, reverse)
    failed = set()
    states = 0
    generated = 0

    def visit(placements, occupied):
        nonlocal states, generated
        states += 1
        if len(placements) == cluster_size:
            return placements
        signature = (len(placements), occupied)
        if signature in failed:
            return None
        candidates = adjacent_placements(target, occupied, orientation_keys, reverse)
        generated += len(candidates)
        for placed in candidates:
            result = visit((*placements, placed), occupied.union(placed))
            if result is not None:
                return result
        failed.add(signature)
        return None

    for root in roots:
        witness = visit((root,), root)
        if witness is not None:
            return {
                "result": "sat",
                "witness": witness,
                "root_placements": len(roots),
                "states": states,
                "failed_states": len(failed),
                "generated_placements": generated,
            }
    return {
        "result": "unsat",
        "witness": None,
        "root_placements": len(roots),
        "states": states,
        "failed_states": len(failed),
        "generated_placements": generated,
    }


def first_local_obstruction(target, orientation_keys, max_cells=None):
    ordered = sorted(
        target,
        key=lambda cell: (sum(neighbor in target for neighbor in atomic_neighbors(cell)), cell),
    )
    cells_checked = 0
    states = 0
    for cell in ordered:
        result = connected_cluster_covering_cell(target, cell, orientation_keys)
        cells_checked += 1
        states += result["states"]
        if result["result"] == "unsat":
            replay = connected_cluster_covering_cell(
                target, cell, orientation_keys, reverse=True
            )
            return {
                "verified": replay["result"] == "unsat",
                "method": "exhaustive_on_demand_connected_four_copy_growth_with_reverse_order_replay",
                "uncovered_cell": list(cell),
                "target_cells_checked": cells_checked,
                "forward": {key: value for key, value in result.items() if key != "witness"},
                "reverse_replay": {key: value for key, value in replay.items() if key != "witness"},
                "states_before_obstruction": states,
            }
        if max_cells is not None and cells_checked >= max_cells:
            break
    return None


def first_atomic_coverage_obstruction(target, orientation_keys):
    ordered = sorted(
        target,
        key=lambda cell: (sum(neighbor in target for neighbor in atomic_neighbors(cell)), cell),
    )
    for checked, cell in enumerate(ordered, 1):
        forward = placements_covering_cell(target, cell, orientation_keys)
        if forward:
            continue
        reverse = placements_covering_cell(target, cell, orientation_keys, reverse=True)
        return {
            "v": 1,
            "verified": not reverse,
            "method": "exhaustive_contained_monotile_coverage_with_reverse_replay",
            "cell": list(cell), "cells_checked": checked,
            "forward": [len(forward)], "reverse": [len(reverse)],
        }
    return None


def contained_atomic_placements(target, orientation_keys):
    placements = {
        placed
        for cell in target
        for placed in anchored_placements(cell, orientation_keys)
        if placed.issubset(target)
    }
    return [{"cells": placed} for placed in sorted(
        placements, key=lambda cells: tuple(sorted(cells))
    )]


def placement_graph_from_contained(target, placements):
    cell_sets = [set(placement["cells"]) for placement in placements]
    cell_index = {cell: index for index, cell in enumerate(sorted(target))}
    cell_masks = [
        sum(1 << cell_index[cell] for cell in cells)
        for cells in cell_sets
    ]
    by_cell = {cell: [] for cell in target}
    for index, cells in enumerate(cell_sets):
        for cell in cells:
            by_cell[cell].append(index)
    adjacency = [set() for _ in placements]
    candidate_pairs = set()
    for left, cells in enumerate(cell_sets):
        boundary = {
            neighbor
            for cell in cells
            for neighbor in atomic_neighbors(cell)
            if neighbor not in cells and neighbor in target
        }
        for neighbor in boundary:
            for right in by_cell[neighbor]:
                if right <= left:
                    continue
                candidate_pairs.add((left, right))
                if cell_masks[left] & cell_masks[right] == 0:
                    adjacency[left].add(right)
                    adjacency[right].add(left)
    graph_sha256 = hashlib.sha256(json.dumps({
        "placements": [sorted(placement["cells"]) for placement in placements],
        "adjacency": [sorted(neighbors) for neighbors in adjacency],
    }, separators=(",", ":")).encode()).hexdigest()
    return {
        "placements": placements, "cell_sets": cell_sets,
        "cell_index": cell_index, "cell_masks": cell_masks,
        "adjacency": adjacency, "by_cell": by_cell,
        "adjacency_candidate_pairs": len(candidate_pairs), "sha256": graph_sha256,
    }


def graph_connected_four_witness(graph, root, reverse=False):
    masks = graph["cell_masks"]
    adjacency = graph["adjacency"]
    states = 0
    failed = set()

    def visit(group, occupied):
        nonlocal states
        states += 1
        if len(group) == 4:
            return tuple(group)
        signature = frozenset(group)
        if signature in failed:
            return None
        frontier = set().union(*(adjacency[index] for index in group)).difference(group)
        for candidate in sorted(frontier, reverse=reverse):
            if masks[candidate] & occupied:
                continue
            result = visit((*group, candidate), occupied | masks[candidate])
            if result is not None:
                return result
        failed.add(signature)
        return None

    witness = visit((root,), masks[root])
    return witness, states, len(failed)


def graph_local_obstruction(target, graph):
    ordered_cells = sorted(
        target,
        key=lambda cell: (sum(neighbor in target for neighbor in atomic_neighbors(cell)), cell),
    )

    def find_uncovered(reverse, only_cell=None):
        status = {}
        states = 0
        failed = 0
        checked = 0
        cells = [only_cell] if only_cell is not None else ordered_cells
        for cell in cells:
            checked += 1
            roots = sorted(graph["by_cell"][cell], reverse=reverse)
            covered = False
            for root in roots:
                if root not in status:
                    witness, root_states, root_failed = graph_connected_four_witness(
                        graph, root, reverse
                    )
                    states += root_states
                    failed += root_failed
                    status[root] = witness is not None
                    if witness is not None:
                        for member in witness:
                            status[member] = True
                if status[root]:
                    covered = True
                    break
            if not covered:
                return cell, checked, status, states, failed
        return None, checked, status, states, failed

    uncovered, checked, forward_status, forward_states, forward_failed = find_uncovered(False)
    if uncovered is None:
        return None
    replay_cell, _, reverse_status, reverse_states, reverse_failed = find_uncovered(
        True, only_cell=uncovered
    )
    return {
        "v": 1,
        "verified": replay_cell == uncovered,
        "method": "exhaustive_placement_graph_connected_four_coverage_with_reverse_replay",
        "cell": list(uncovered),
        "cells_checked": checked,
        "monotile_placements": len(graph["placements"]),
        "placement_graph_sha256": graph["sha256"],
        "forward": [len(forward_status), forward_states, forward_failed],
        "reverse": [len(reverse_status), reverse_states, reverse_failed],
    }


def connected_groups(selected, adjacency, group_size=4):
    selected_set = set(selected)
    groups = set()
    for root in sorted(selected):
        frontier = {frozenset((root,))}
        for _ in range(1, group_size):
            following = set()
            for group in frontier:
                neighbors = set().union(*(adjacency[index] for index in group))
                for neighbor in neighbors.intersection(selected_set).difference(group):
                    following.add(group.union((neighbor,)))
            frontier = following
        groups.update(frontier)
    return sorted(tuple(sorted(group)) for group in groups)


def partition_selected(selected, adjacency, group_size=4):
    groups = connected_groups(selected, adjacency, group_size)
    by_placement = {index: [] for index in selected}
    for group in groups:
        for index in group:
            by_placement[index].append(group)
    failed = set()

    def visit(remaining):
        if not remaining:
            return []
        signature = frozenset(remaining)
        if signature in failed:
            return None
        count, pivot, legal = min(
            (
                len([group for group in by_placement[index] if all(x in remaining for x in group)]),
                index,
                [group for group in by_placement[index] if all(x in remaining for x in group)],
            )
            for index in remaining
        )
        if count == 0:
            failed.add(signature)
            return None
        for group in legal:
            suffix = visit(remaining.difference(group))
            if suffix is not None:
                return [group, *suffix]
        failed.add(signature)
        return None

    solution = visit(set(selected))
    return {
        "result": "sat" if solution is not None else "unsat",
        "solution": solution,
        "connected_groups": len(groups),
        "failed_states": len(failed),
    }


def compact_exact_cover(target, graph, timeout_ms, max_models=256):
    started = time.monotonic()
    variables = [Bool(f"four_atomic_{index}") for index in range(len(graph["placements"]))]
    solver = SolverFor("QF_FD")
    for cell in sorted(target):
        solver.add(PbEq([(variables[index], 1) for index in graph["by_cell"][cell]], 1))
    attempts = []
    for model_index in range(max_models):
        remaining_ms = timeout_ms - round((time.monotonic() - started) * 1000)
        if remaining_ms <= 0:
            return {"result": "unknown", "stopped_by": "time_limit", "attempts": attempts}
        solver.set(timeout=remaining_ms)
        outcome = solver.check()
        if outcome == unsat:
            return {"result": "unsat", "attempts": attempts}
        if outcome != sat:
            return {"result": "unknown", "stopped_by": "solver_timeout", "attempts": attempts}
        model = solver.model()
        selected = [
            index for index, variable in enumerate(variables)
            if is_true(model.eval(variable))
        ]
        partition = partition_selected(selected, graph["adjacency"])
        attempts.append({
            "selected_monotiles": len(selected),
            "connected_groups": partition["connected_groups"],
            "failed_states": partition["failed_states"],
            "result": partition["result"],
        })
        if partition["result"] == "sat":
            return {
                "result": "sat", "selected": selected,
                "groups": partition["solution"], "attempts": attempts,
            }
        solver.add(Or([
            Not(variable) if index in selected else variable
            for index, variable in enumerate(variables)
        ]))
    return {"result": "unknown", "stopped_by": "model_limit", "attempts": attempts}


def replay_unsat_with_forward_algorithm_x(target, placements, timeout_ms):
    ordered_target = sorted(target)
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
            choices.append((len(legal), cell_index, legal))
            remaining ^= lowest
        _, _, legal = min(choices)
        for placement_index in legal:
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
        "method": "independent_forward_order_algorithm_x",
        "result": result,
        "placements": len(placements), "constraints": len(target),
        "nodes": nodes, "failed_states": len(failed), "timeout_ms": timeout_ms,
    }


def screen_parent(packed, record, orientation_keys, timeout_ms, replay_timeout_ms):
    parent_cells = FOUR.cells_as_dicts(FOUR.unpack_key(packed))
    target = scaled_parent_cells(parent_cells, 2)
    atomic_obstruction = first_atomic_coverage_obstruction(target, orientation_keys)
    if atomic_obstruction is not None:
        if not atomic_obstruction["verified"]:
            raise RuntimeError("four-copy atomic coverage replay failed")
        return "local_obstruction", atomic_obstruction
    atomic_placements = contained_atomic_placements(target, orientation_keys)
    graph = placement_graph_from_contained(target, atomic_placements)
    graph_obstruction = graph_local_obstruction(target, graph)
    if graph_obstruction is not None:
        if not graph_obstruction["verified"]:
            raise RuntimeError("four-copy graph local obstruction replay failed")
        return "local_obstruction", graph_obstruction
    atomic_placements = graph["placements"]
    atomic_prefilter = THREE.replay_unsat_with_independent_algorithm_x(
        target, atomic_placements, timeout_ms
    )
    if atomic_prefilter["result"] == "unsat":
        replay = replay_unsat_with_forward_algorithm_x(
            target, atomic_placements, replay_timeout_ms
        )
        return (
            "exact_unsat" if replay["verified"] else "unresolved",
            {
                "method": "reverse_and_forward_order_atomic_algorithm_x",
                "monotile_placements": len(atomic_placements),
                "primary_exact": atomic_prefilter,
                "exact_unsat_replay": replay,
            },
        )
    compact = compact_exact_cover(target, graph, timeout_ms)
    common = {
        "method": "compact_atomic_cover_with_connected_four_partition_cegar",
        "placement_graph_sha256": graph["sha256"],
        "monotile_placements": len(graph["placements"]),
        "compact": compact,
    }
    if compact["result"] == "unsat":
        replay = THREE.replay_unsat_with_independent_algorithm_x(
            target, graph["placements"], replay_timeout_ms
        )
        if not replay["verified"]:
            replay = THREE.replay_unsat_with_qffd(
                target, graph["placements"], replay_timeout_ms
            )
        return (
            "exact_unsat" if replay["verified"] else "unresolved",
            {**common, "exact_unsat_replay": replay},
        )
    if compact["result"] == "sat":
        child_keys = []
        for group in compact["groups"]:
            cells = frozenset().union(*(graph["cell_sets"][index] for index in group))
            child_keys.append(FOUR.packed_canonical_key(cells).hex())
        covered = set().union(*(
            graph["cell_sets"][index] for index in compact["selected"]
        ))
        replay = {
            "verified": covered == target and len(compact["groups"]) == 8,
            "covered_cells": len(covered), "target_cells": len(target),
            "child_metatiles": len(compact["groups"]),
        }
        return "mixed_metatile_rule", {**common, "child_keys": child_keys, "replay": replay}
    return "unresolved", {**common, "stopped_by": compact.get("stopped_by")}


def compact_receipt(classification, receipt):
    if classification != "local_obstruction":
        return receipt
    if receipt.get("v") == 1:
        return receipt
    forward = receipt["forward"]
    reverse = receipt["reverse_replay"]
    return {
        "v": 1,
        "verified": receipt["verified"],
        "method": "on_demand_connected_four_reverse_replay",
        "cell": receipt["uncovered_cell"],
        "cells_checked": receipt["target_cells_checked"],
        "forward": [
            forward["root_placements"], forward["states"],
            forward["failed_states"], forward["generated_placements"],
        ],
        "reverse": [
            reverse["root_placements"], reverse["states"],
            reverse["failed_states"], reverse["generated_placements"],
        ],
    }


def ensure_screen_schema(connection, record):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS screen_results (
          key BLOB PRIMARY KEY REFERENCES four_keys(key),
          classification TEXT NOT NULL,
          receipt TEXT NOT NULL
        )
    """)
    meta = dict(connection.execute("SELECT name, value FROM meta"))
    if meta.get("candidate_id") != record["id"]:
        raise RuntimeError("screen database candidate mismatch")
    if int(meta["bases_completed"]) != int(meta["three_copy_types"]):
        raise RuntimeError("four-copy enumeration is not complete")
    connection.commit()


def finish_report(connection, record):
    total = connection.execute("SELECT COUNT(*) FROM four_keys").fetchone()[0]
    completed = connection.execute("SELECT COUNT(*) FROM screen_results").fetchone()[0]
    counts = dict(connection.execute(
        "SELECT classification, COUNT(*) FROM screen_results GROUP BY classification"
    ))
    digest = hashlib.sha256()
    rules = []
    unresolved = []
    for key, classification, receipt_json in connection.execute(
        "SELECT key, classification, receipt FROM screen_results ORDER BY key"
    ):
        digest.update(key)
        digest.update(b"\0" + classification.encode() + b"\0" + receipt_json.encode() + b"\n")
        if classification == "mixed_metatile_rule":
            rules.append({"parent_key": key.hex(), "receipt": json.loads(receipt_json)})
        elif classification == "unresolved":
            unresolved.append({"parent_key": key.hex(), "receipt": json.loads(receipt_json)})
    rule_map = {entry["parent_key"]: entry["receipt"]["child_keys"] for entry in rules}
    closed_alphabet = None
    for seed in sorted(rule_map):
        closure = {seed}
        frontier = [seed]
        valid = True
        while frontier and valid:
            parent = frontier.pop()
            children = rule_map.get(parent)
            if children is None:
                valid = False
                break
            for child in children:
                if child not in closure:
                    closure.add(child)
                    frontier.append(child)
        if valid and (closed_alphabet is None or len(closure) < len(closed_alphabet)):
            closed_alphabet = sorted(closure)
    certified = completed == total and not unresolved
    if closed_alphabet is not None:
        classification = "four_copy_metatile_substitution_system"
    elif certified and not rules:
        classification = "no_four_copy_metatile_scalar2_substitution"
    else:
        classification = "unresolved"
    meta = dict(connection.execute("SELECT name, value FROM meta"))
    return {
        "id": record["id"], "cells": record["cells"], "classification": classification,
        "four_copy_metatile_screen": {
            "certified": certified, "scale": 2,
            "family": "all_face_connected_four_copy_metatiles_modulo_proper_a2_isometry_and_translation",
            "symmetry_distinct_metatiles": total,
            "canonical_sha256": meta.get("four_copy_sha256"),
            "parents_completed": completed,
            "parent_counts": {
                name: counts.get(name, 0) for name in (
                    "local_obstruction", "exact_unsat", "mixed_metatile_rule", "unresolved"
                )
            },
            "receipt_stream_sha256": digest.hexdigest(),
            "closed_alphabet": closed_alphabet,
            "rules": rules, "unresolved_parents": unresolved,
        },
    }


def screen_database(
    record, database, output, timeout_ms, replay_timeout_ms, progress_every,
    emit_summary=True, shard_index=0, shard_count=1,
):
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid screen shard")
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    ensure_screen_schema(connection, record)
    orientations = SUBSTITUTION.oriented_cells(record["cells"])
    orientation_keys = tuple(
        tuple(SUBSTITUTION.cell_key(cell) for cell in orientation["cells"])
        for orientation in orientations
    )
    total = connection.execute("SELECT COUNT(*) FROM four_keys").fetchone()[0]
    shard_total = connection.execute(
        "SELECT COUNT(*) FROM four_keys WHERE (rowid % ?) = ?",
        (shard_count, shard_index),
    ).fetchone()[0]
    completed = connection.execute("""
        SELECT COUNT(*) FROM four_keys
        JOIN screen_results USING(key)
        WHERE (four_keys.rowid % ?) = ?
    """, (shard_count, shard_index)).fetchone()[0]
    live_counts = dict(connection.execute(
        """SELECT classification, COUNT(*) FROM four_keys
           JOIN screen_results USING(key)
           WHERE (four_keys.rowid % ?) = ? GROUP BY classification""",
        (shard_count, shard_index),
    ))
    next_progress = (
        ((completed // progress_every) + 1) * progress_every
        if progress_every else None
    )
    started = time.monotonic()
    while completed < shard_total:
        rows = connection.execute("""
            SELECT four_keys.key FROM four_keys
            LEFT JOIN screen_results USING(key)
            WHERE screen_results.key IS NULL
              AND (four_keys.rowid % ?) = ?
            ORDER BY four_keys.key LIMIT 1000
        """, (shard_count, shard_index)).fetchall()
        if not rows:
            break
        pending = []
        for (key,) in rows:
            classification, receipt = screen_parent(
                key, record, orientation_keys, timeout_ms, replay_timeout_ms
            )
            receipt = compact_receipt(classification, receipt)
            pending.append((
                key, classification, json.dumps(receipt, separators=(",", ":"))
            ))
            completed += 1
            live_counts[classification] = live_counts.get(classification, 0) + 1
            if next_progress is not None and completed >= next_progress:
                print(
                    f"{record['id']} shard {shard_index + 1}/{shard_count} "
                    f"screened {completed}/{shard_total} {live_counts} "
                    f"elapsed_s {round(time.monotonic() - started, 1)}",
                    flush=True,
                )
                next_progress += progress_every
        connection.executemany(
            "INSERT OR IGNORE INTO screen_results(key, classification, receipt) VALUES (?, ?, ?)",
            pending,
        )
        connection.commit()
    connection.commit()
    global_completed = connection.execute("SELECT COUNT(*) FROM screen_results").fetchone()[0]
    report = finish_report(connection, record) if global_completed == total else None
    if report is not None:
        output.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    connection.close()
    if emit_summary and report is not None:
        print(json.dumps(report["four_copy_metatile_screen"], indent=2))
    elif emit_summary:
        print(json.dumps({
            "id": record["id"], "shard": [shard_index, shard_count],
            "shard_completed": completed, "shard_total": shard_total,
            "global_completed": global_completed, "global_total": total,
        }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--replay-timeout-ms", type=int, default=300000)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    record = next(record for record in records if record["id"] == args.id)
    screen_database(
        record, Path(args.database), Path(args.output), args.timeout_ms,
        args.replay_timeout_ms, args.progress_every,
        shard_index=args.shard_index, shard_count=args.shard_count,
    )


if __name__ == "__main__":
    main()
