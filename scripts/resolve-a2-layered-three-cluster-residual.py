#!/usr/bin/env python3
"""Independently resolve and seal one three-cluster report residual."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


THREE = load("a2_three_cluster", "screen-a2-layered-three-cluster-substitution.py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--parent-index", type=int, required=True)
    parser.add_argument("--timeout-ms", type=int, default=300000)
    args = parser.parse_args()

    report_path = Path(args.report)
    report = json.loads(report_path.read_text())
    source = next(
        record
        for record in (
            json.loads(line) for line in Path(args.input).read_text().splitlines()
            if line.strip()
        )
        if record["id"] == report["id"]
    )
    screen = report["three_copy_metatile_screen"]
    scale = screen.get("scale")
    if scale is None:
        scale = int(screen["inflation"].removeprefix("scalar_"))
    enumerated = THREE.enumerate_three_copy_metatiles(source)
    if enumerated["symmetry_distinct_metatiles"] != screen["symmetry_distinct_metatiles"]:
        raise RuntimeError("three-copy metatile count changed during residual replay")
    if enumerated["canonical_sha256"] != screen["canonical_sha256"]:
        raise RuntimeError("three-copy metatile family hash changed during residual replay")

    parent_result = screen["parent_results"][args.parent_index]
    if parent_result["parent_index"] != args.parent_index:
        raise RuntimeError("parent result order mismatch")
    if parent_result.get("primary_exact_result") != "unsat":
        raise RuntimeError("residual does not carry a primary exact UNSAT result")

    parent = enumerated["metatiles"][args.parent_index]
    target = THREE.SUBSTITUTION.scaled_cells(parent["cells"], scale)
    tile_orientations = THREE.SUBSTITUTION.oriented_cells(source["cells"])
    graph = THREE.placement_graph(target, tile_orientations)
    uncovered, _ = THREE.first_uncovered_by_three_cluster(target, graph)
    if uncovered is not None:
        raise RuntimeError("residual unexpectedly acquired a local obstruction")
    placements = THREE.all_connected_triple_placements(graph)
    if len(placements) != parent_result["three_cluster_placements"]:
        raise RuntimeError("residual child-placement count changed")
    replay = THREE.replay_unsat_with_independent_algorithm_x(
        target, placements, args.timeout_ms
    )
    if not replay["verified"]:
        raise RuntimeError(f"residual remains unresolved: {replay}")

    prior_replay = parent_result.get("exact_unsat_replay")
    parent_result["classification"] = "exact_unsat"
    parent_result["prior_exact_unsat_replay"] = prior_replay
    parent_result["algorithm_x_replay"] = replay
    parent_result["exact_unsat_replay"] = replay
    parent_result.pop("stopped_by", None)

    names = ("local_obstruction", "exact_unsat", "mixed_metatile_rule", "unresolved")
    screen["parent_counts"] = {
        name: sum(result["classification"] == name for result in screen["parent_results"])
        for name in names
    }
    if screen["parent_counts"]["mixed_metatile_rule"] or screen["parent_counts"]["unresolved"]:
        raise RuntimeError("report still contains a rule or unresolved parent")
    screen["certified"] = True
    screen.setdefault("residual_resolutions", []).append({
        "parent_index": args.parent_index,
        "family_sha256": screen["canonical_sha256"],
        "prior_replay": prior_replay,
        "resolution": replay,
    })
    report["classification"] = f"no_three_copy_metatile_scalar{scale}_substitution"
    report_path.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({
        "id": report["id"],
        "parent_index": args.parent_index,
        "classification": report["classification"],
        "parent_counts": screen["parent_counts"],
        "resolution": replay,
        "report": str(report_path),
    }, indent=2))


if __name__ == "__main__":
    main()
