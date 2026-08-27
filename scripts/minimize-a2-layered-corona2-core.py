#!/usr/bin/env python3
"""Greedily shrink and independently replay an A2 radius-two UNSAT core."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEOMETRY = load("a2_periodic_z3", "screen-a2-layered-periodic-z3.py")
CORONA = load("a2_corona_z3", "screen-a2-layered-corona-z3.py")
CORE = load("a2_corona2_core", "screen-a2-layered-corona2-core-cegar.py")


def load_record(path, candidate_id):
    records = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    matches = [record for record in records if record["id"] == candidate_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {candidate_id!r} record in {path}, found {len(matches)}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--source-core", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--clause", type=int, default=0)
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--indices", default="")
    parser.add_argument("--no-greedy", action="store_true")
    args = parser.parse_args()

    record = load_record(args.input, args.id)
    source = load_record(args.source_core, args.id)
    clause = source["corona2_core_cegar"]["clauses"][args.clause]
    source_indices = list(clause["outer_placement_indices"])
    original = (
        [int(value) for value in args.indices.split(",") if value]
        if args.indices else list(source_indices)
    )
    if not set(original).issubset(source_indices):
        raise ValueError("--indices must be a subset of the source clause")

    root = GEOMETRY.tile_occupancy(record["cells"])
    orientations = GEOMETRY.orientations(root)
    first = CORONA.candidate_placements(root, orientations)

    def check(indices, label):
        selected = [first[index] for index in indices]
        started = time.monotonic()
        result = CORE.extension_with_core(
            root, orientations, selected, args.timeout_ms, label
        )
        return {
            "result": result["result"],
            "milliseconds": round((time.monotonic() - started) * 1000),
            "placements_considered": result["placements_considered"],
        }

    initial = check(original, "core_replay_initial")
    if initial["result"] != "unsat":
        raise RuntimeError(f"source core did not replay as UNSAT: {initial}")

    current = list(original)
    attempts = []
    for placement_index in ([] if args.no_greedy else original):
        if placement_index not in current:
            continue
        trial = [index for index in current if index != placement_index]
        result = check(trial, f"core_replay_without_{placement_index}")
        removed = result["result"] == "unsat"
        attempts.append({
            "removed_placement_index": placement_index,
            "remaining_size": len(trial),
            "proved_redundant": removed,
            **result,
        })
        if removed:
            current = trial
        print(
            f"remove {placement_index}: {result['result']} "
            f"({result['milliseconds']} ms), core size {len(current)}",
            flush=True,
        )

    final = check(current, "core_replay_final")
    certified_by = "final_replay"
    if final["result"] != "unsat":
        successful_steps = [attempt for attempt in attempts if attempt["proved_redundant"]]
        if not successful_steps or successful_steps[-1]["remaining_size"] != len(current):
            raise RuntimeError(f"reduced core did not replay as UNSAT: {final}")
        certified_by = "last_successful_reduction_step"

    output = {
        "id": args.id,
        "classification": "sound_radius2_placement_obstruction",
        "source": str(args.source_core),
        "source_clause": args.clause,
        "source_outer_placement_indices": source_indices,
        "original_outer_placement_indices": original,
        "reduced_outer_placement_indices": current,
        "original_size": len(original),
        "reduced_size": len(current),
        "minimal": (not args.no_greedy) and bool(attempts) and all(
            attempt["result"] == "sat" for attempt in attempts
            if not attempt["proved_redundant"]
        ),
        "initial_replay": initial,
        "reduction_attempts": attempts,
        "final_replay": final,
        "certified_by": certified_by,
        "timeout_ms_per_check": args.timeout_ms,
        "meaning": (
            "Every first corona containing all reduced placements is unable to "
            "extend to exact saturation of that support; placements outside the "
            "subset remained available as helpers in every UNSAT proof."
        ),
    }
    Path(args.output).write_text(json.dumps(output, separators=(",", ":")) + "\n")
    print(json.dumps({
        "id": args.id,
        "original_size": len(original),
        "reduced_size": len(current),
        "minimal": output["minimal"],
        "output": args.output,
    }, indent=2))


if __name__ == "__main__":
    main()
