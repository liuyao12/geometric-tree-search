#!/usr/bin/env python3
"""Extend independently replayed A2-sliced corona patches by one exact layer."""

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


def source_patch(record: dict) -> tuple[int, list[dict], str]:
    """Return (completed radius, patch, receipt field) from a replayed witness."""
    extension = record.get("patch_extension", {})
    if (record.get("patch_extension_classification", "").endswith("_witness")
            and extension.get("replay", {}).get("verified")):
        return (
            int(extension["target_radius"]),
            extension["source_patch"] + extension["added_patch"],
            "patch_extension",
        )
    retained = record.get("retained_corona_extension", {})
    if (record.get("retained_corona_extension_classification") == "radius2_witness"
            and retained.get("replay", {}).get("verified")):
        return 2, retained["first_patch"] + retained["added_patch"], "retained_corona_extension"
    cegar = record.get("corona2_cegar", {})
    if (record.get("corona2_classification") == "radius2_witness"
            and cegar.get("replay", {}).get("verified")):
        return 2, cegar["first_patch"] + cegar["added_patch"], "corona2_cegar"
    raise ValueError(f"{record.get('id')} lacks an independently replayed source patch")


def screen(record: dict, timeout_ms: int, backend: str) -> dict:
    started = time.monotonic()
    radius, patch, source_field = source_patch(record)
    root = GEOMETRY.record_occupancy(record)
    orientations = GEOMETRY.orientations(root)
    root_key = (0, (0, 0, 0))
    selected = []
    seen = {root_key}
    for placement in patch:
        key = (placement["orientation_index"], tuple(placement["translation"]))
        if key == root_key or key in seen:
            continue
        seen.add(key)
        selected.append({
            "orientation_index": key[0],
            "translation": list(key[1]),
            "occupancy": CORONA.translated_occupancy(
                orientations[key[0]]["occupancy"], key[1]
            ),
        })
    normalized_patch = [{"orientation_index": 0, "translation": [0, 0, 0]}] + [
        {"orientation_index": placement["orientation_index"],
         "translation": placement["translation"]}
        for placement in selected
    ]
    target_radius = radius + 1
    extension = CORE.extension_with_core(
        root, orientations, selected, timeout_ms,
        f"radius{target_radius}_{record['id']}", backend,
    )
    common = {
        "source_radius": radius,
        "target_radius": target_radius,
        "source_field": source_field,
        "source_patch_copies": len(normalized_patch),
        "placements_considered": extension["placements_considered"],
        "milliseconds": round((time.monotonic() - started) * 1000),
    }
    if extension["result"] == "sat":
        patch_keys = {
            (placement["orientation_index"], tuple(placement["translation"]))
            for placement in normalized_patch
        }
        added = [
            {
                "orientation_index": extension["final"][index]["orientation_index"],
                "translation": extension["final"][index]["translation"],
            }
            for index in extension["selected"]
            if (extension["final"][index]["orientation_index"],
                tuple(extension["final"][index]["translation"])) not in patch_keys
        ]
        replay = CEGAR.replay_extension(orientations, normalized_patch, added)
        if not replay["verified"]:
            raise RuntimeError(f"radius-{target_radius} replay failed: {replay}")
        return {
            **record,
            "patch_extension_classification": f"radius{target_radius}_witness",
            "patch_extension": {
                **common,
                "source_patch": normalized_patch,
                "added_patch": added,
                "replay": replay,
            },
        }
    if extension["result"] == "unsat":
        return {
            **record,
            "patch_extension_classification": "source_patch_unextendible",
            "patch_extension": {
                **common,
                "claim_scope": "this_replayed_source_patch_only",
                "unsat_core_source_indices": extension["core"],
            },
        }
    return {
        **record,
        "patch_extension_classification": "unresolved",
        "patch_extension": {**common, "stopped_by": "solver_timeout"},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--timeout-ms", type=int, default=300000)
    parser.add_argument("--backend", choices=("z3", "qffd"), default="qffd")
    args = parser.parse_args()
    requested = {value for value in args.ids.split(",") if value}
    records = []
    for filename in args.input:
        records.extend(json.loads(line) for line in Path(filename).read_text().splitlines()
                       if line.strip())
    if requested:
        records = [record for record in records if record["id"] in requested]
    output = Path(args.output)
    output.write_text("")
    counts: dict[str, int] = {}
    with output.open("a") as stream:
        for index, record in enumerate(records, 1):
            result = screen(record, args.timeout_ms, args.backend)
            classification = result["patch_extension_classification"]
            counts[classification] = counts.get(classification, 0) + 1
            stream.write(json.dumps(result, separators=(",", ":")) + "\n")
            stream.flush()
            print(f"{index}/{len(records)} {record['id']} {classification}", flush=True)
    print(json.dumps({"records": len(records), "counts": counts,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
