#!/usr/bin/env python3
"""Exact mixed substitution screen for face-connected three-copy alcove metatiles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TWO = load("a2_sliced_two_cluster", "screen-a2-sliced-two-cluster-substitution.py")
SUB = TWO.SUB


def enumerate_three_copy_metatiles(record, include_reflections=False):
    """Enumerate every connected three-copy union modulo the selected A2 group."""
    prototile = record["alcoves"]
    orientations = SUB.oriented_cells(prototile, include_reflections)
    two = TWO.enumerate_two_copy_metatiles(record, include_reflections)
    representatives = {}
    raw = 0
    for two_index, metatile in enumerate(two["metatiles"]):
        cluster = metatile["alcoves"]
        occupied = {SUB.cell_key(cell) for cell in cluster}
        for neighbor in TWO.adjacent_atomic_cells(cluster):
            neighbor_key = SUB.cell_key(neighbor)
            for orientation_index, orientation in enumerate(orientations):
                for own_cell in orientation["cells"]:
                    own_key = SUB.cell_key(own_cell)
                    if own_key[3] != neighbor_key[3]:
                        continue
                    delta = tuple(neighbor_key[axis] - own_key[axis] for axis in range(3))
                    partner = TWO.translated_cells(orientation["cells"], delta)
                    partner_keys = {SUB.cell_key(cell) for cell in partner}
                    if occupied.intersection(partner_keys):
                        continue
                    raw += 1
                    union = [*cluster, *partner]
                    key = TWO.canonical_key(union, include_reflections)
                    if key in representatives:
                        continue
                    replay = TWO.replay_base_decomposition(cluster, partner, union)
                    if not replay["verified"]:
                        raise RuntimeError(f"three-copy base replay failed: {replay}")
                    representatives[key] = {
                        "alcoves": union,
                        "canonical_key": [list(cell) for cell in key],
                        "base_decomposition": {
                            "two_copy_parent_index": two_index,
                            "partner_orientation_index": orientation_index,
                            "partner_translation": list(delta),
                            "replay": replay,
                        },
                    }
    metatiles = [representatives[key] for key in sorted(representatives)]
    digest = hashlib.sha256(json.dumps(
        [item["canonical_key"] for item in metatiles], separators=(",", ":")
    ).encode()).hexdigest()
    return {
        "raw_connected_extensions": raw,
        "symmetry_distinct_metatiles": len(metatiles),
        "canonical_sha256": digest,
        "metatiles": metatiles,
    }


def screen_candidate(record, scale, timeout_ms, include_reflections=False,
                     max_parents=0):
    enumerated = enumerate_three_copy_metatiles(record, include_reflections)
    metatiles = enumerated["metatiles"]
    alphabet = TWO.oriented_alphabet(metatiles, include_reflections)
    atomic_alphabet = TWO.oriented_alphabet(
        [{"alcoves": record["alcoves"]}], include_reflections)
    limit = min(len(metatiles), max_parents) if max_parents > 0 else len(metatiles)
    results = []
    for parent_index, parent in enumerate(metatiles[:limit]):
        target = SUB.inflated_cells(parent["alcoves"], scale)
        atomic_placements = TWO.mixed_placements(target, atomic_alphabet)
        atomic_covered = (set().union(*(placement["cells"] for placement in atomic_placements))
                          if atomic_placements else set())
        atomic_uncovered = next(
            (cell for cell in sorted(target) if cell not in atomic_covered), None)
        if atomic_uncovered is not None:
            replay = TWO.replay_local_obstruction(
                target, atomic_alphabet, atomic_uncovered)
            if not replay["verified"]:
                raise RuntimeError(f"atomic local obstruction replay failed: {replay}")
            results.append({
                "parent_index": parent_index,
                "classification": "atomic_local_obstruction",
                "target_alcoves": len(target),
                "atomic_local_obstruction_replay": replay,
            })
            continue
        placements = TWO.mixed_placements(target, alphabet)
        covered = set().union(*(placement["cells"] for placement in placements)) if placements else set()
        uncovered = next((cell for cell in sorted(target) if cell not in covered), None)
        if uncovered is not None:
            replay = TWO.replay_local_obstruction(target, alphabet, uncovered)
            if not replay["verified"]:
                raise RuntimeError(f"local obstruction replay failed: {replay}")
            results.append({
                "parent_index": parent_index,
                "classification": "local_obstruction",
                "target_alcoves": len(target),
                "local_obstruction_replay": replay,
            })
            continue
        solved = SUB.exact_cover(target, placements, timeout_ms)
        common = {
            "parent_index": parent_index,
            "target_alcoves": len(target),
            "placements_considered": len(placements),
            "nodes": solved["nodes"],
            "failed_states": solved["failed_states"],
        }
        if solved["result"] == "sat":
            replay = SUB.replay(target, placements, solved["solution"], scale ** 3)
            if not replay["verified"]:
                raise RuntimeError(f"mixed rule replay failed: {replay}")
            results.append({
                **common,
                "classification": "mixed_metatile_rule",
                "rule": [{
                    "type_index": placements[index]["type_index"],
                    "orientation_index": placements[index]["orientation_index"],
                    "translation": placements[index]["translation"],
                } for index in solved["solution"]],
                "replay": replay,
            })
        elif solved["result"] == "unsat":
            replay = SUB.replay_unsat_with_z3(target, placements, timeout_ms)
            if not replay["verified"]:
                raise RuntimeError(f"mixed UNSAT replay failed: {replay}")
            results.append({**common, "classification": "exact_unsat",
                            "exact_unsat_replay": replay})
        else:
            results.append({**common, "classification": "unresolved",
                            "stopped_by": "time_limit"})

    rules = {result["parent_index"]: result for result in results
             if result["classification"] == "mixed_metatile_rule"}
    closed = None
    for seed in sorted(rules):
        closure = {seed}
        frontier = [seed]
        valid = True
        while frontier and valid:
            rule = rules.get(frontier.pop())
            if rule is None:
                valid = False
                break
            for child in rule["rule"]:
                if child["type_index"] not in closure:
                    closure.add(child["type_index"])
                    frontier.append(child["type_index"])
        if valid and (closed is None or len(closure) < len(closed)):
            closed = sorted(closure)
    complete = limit == len(metatiles)
    unknowns = [result for result in results if result["classification"] == "unresolved"]
    if closed is not None:
        classification = "three_copy_metatile_substitution_system"
        certified = True
    elif complete and not rules and not unknowns:
        classification = f"no_three_copy_metatile_scalar{scale}_substitution"
        certified = True
    else:
        classification = "unresolved"
        certified = False
    return {
        "id": record["id"],
        "classification": classification,
        "three_copy_alcove_metatile_screen": {
            "certified": certified,
            "scale": scale,
            "include_reflections": include_reflections,
            "family": "all_face_connected_three_copy_metatiles_modulo_selected_a2_group",
            **{key: enumerated[key] for key in (
                "raw_connected_extensions", "symmetry_distinct_metatiles",
                "canonical_sha256")},
            "oriented_metatile_types": len(alphabet),
            "parents_completed": len(results),
            "closed_alphabet": closed,
            "parent_counts": {kind: sum(result["classification"] == kind for result in results)
                              for kind in ("atomic_local_obstruction", "local_obstruction", "exact_unsat",
                                           "mixed_metatile_rule", "unresolved")},
            "parent_results": results,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--include-reflections", action="store_true")
    parser.add_argument("--max-parents", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.input).read_text().splitlines()
               if line.strip()]
    records = records[max(0, args.offset):]
    if args.limit > 0:
        records = records[:args.limit]
    output = Path(args.output)
    output.write_text("")
    counts = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen_candidate(record, args.scale, args.timeout_ms,
                                      args.include_reflections, args.max_parents)
            counts[result["classification"]] = counts.get(result["classification"], 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            detail = result["three_copy_alcove_metatile_screen"]
            print(f"{index}/{len(records)} {record['id']} {result['classification']} "
                  f"({detail['symmetry_distinct_metatiles']} types, "
                  f"{detail['parents_completed']} parents)", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
