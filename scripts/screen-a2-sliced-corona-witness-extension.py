#!/usr/bin/env python3
"""Try to extend each retained, independently replayed first-corona witness."""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path


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


def screen(record: dict, timeout_ms: int, backend: str) -> dict:
    started = time.monotonic()
    root = GEOMETRY.record_occupancy(record)
    orientations = GEOMETRY.orientations(root)
    witness = record.get("corona_z3", {}).get("witness")
    replay = record.get("corona_z3", {}).get("replay", {})
    if not witness or not replay.get("verified"):
        raise ValueError(f"{record['id']} lacks a verified first-corona witness")
    selected = []
    for placement in witness:
        orientation_index = placement["orientation_index"]
        translation = tuple(placement["translation"])
        selected.append({
            "orientation_index": orientation_index,
            "translation": list(translation),
            "occupancy": CORONA.translated_occupancy(
                orientations[orientation_index]["occupancy"], translation
            ),
        })
    first_universe = CORONA.candidate_placements(root, orientations)
    outer_index = {
        (placement["orientation_index"], tuple(placement["translation"])): index
        for index, placement in enumerate(first_universe)
    }
    selected_outer_indices = [
        outer_index[(placement["orientation_index"], tuple(placement["translation"]))]
        for placement in selected
    ]
    extension = CORE.extension_with_core(
        root, orientations, selected, timeout_ms, f"retained_{record['id']}", backend
    )
    common = {
        "source_first_patch_copies": 1 + len(selected),
        "placements_considered": extension["placements_considered"],
        "milliseconds": round((time.monotonic() - started) * 1000),
    }
    if extension["result"] == "sat":
        first_patch = [{"orientation_index": 0, "translation": [0, 0, 0]}] + [
            {"orientation_index": placement["orientation_index"],
             "translation": placement["translation"]}
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
            if (extension["final"][index]["orientation_index"],
                tuple(extension["final"][index]["translation"])) not in first_keys
        ]
        checked = CEGAR.replay_extension(orientations, first_patch, added)
        if not checked["verified"]:
            raise RuntimeError(f"radius-two witness replay failed: {checked}")
        return {
            **record,
            "retained_corona_extension_classification": "radius2_witness",
            "retained_corona_extension": {
                **common,
                "first_patch": first_patch,
                "added_patch": added,
                "replay": checked,
            },
        }
    if extension["result"] == "unsat":
        core_outer_indices = [selected_outer_indices[index] for index in extension["core"]]
        return {
            **record,
            "retained_corona_extension_classification": "retained_corona_unextendible",
            "retained_corona_extension": {
                **common,
                "claim_scope": "this_verified_first_corona_only",
                "unsat_core_witness_indices": extension["core"],
                "outer_placement_indices": core_outer_indices,
            },
        }
    return {
        **record,
        "retained_corona_extension_classification": "unresolved",
        "retained_corona_extension": {**common, "stopped_by": "solver_timeout"},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--backend", choices=("z3", "qffd"), default="qffd")
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
    counts: dict[str, int] = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.timeout_ms, args.backend)
            classification = result["retained_corona_extension_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
