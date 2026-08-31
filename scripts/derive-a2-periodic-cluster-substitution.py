#!/usr/bin/env python3
"""Derive and replay scale-two cluster substitutions from periodic quotients."""

from __future__ import annotations

import gzip
import importlib.util
import json
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/a2-sliced-size9-palindromic-periodic-exact8-complete.ndjson.gz"
OUTPUT = ROOT / "data/a2-sliced-size9-palindromic-periodic-cluster-substitutions.ndjson.gz"
BACKEND = ROOT / "scripts/screen-a2-layered-periodic-z3.py"


def load_backend():
    spec = importlib.util.spec_from_file_location("a2_periodic_backend", BACKEND)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def add(*vectors):
    return [sum(vector[axis] for vector in vectors) for axis in range(3)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(SOURCE))
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument("--expected-rules", type=int, default=2)
    args = parser.parse_args()
    backend = load_backend()
    source_path = Path(args.source)
    output_path = Path(args.output)
    with gzip.open(source_path, "rt", encoding="utf8") as source:
        rows = [json.loads(line) for line in source if line.strip()]
    results = []
    for row in rows:
        if row["classification"] != "periodic":
            continue
        certificate = row["periodic_z3"]["certificate"]
        basis = certificate["period_vectors"]
        placements = []
        child_clusters = []
        for bits in ((a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)):
            offset = add(*([basis[index] for index, bit in enumerate(bits) if bit] or [[0, 0, 0]]))
            child = []
            for placement in certificate["placements"]:
                expanded = {
                    "orientation_index": placement["orientation_index"],
                    "translation": add(placement["translation"], offset),
                }
                child.append(expanded)
                placements.append(expanded)
            child_clusters.append({"coset": list(bits), "translation": offset, "placements": child})
        doubled = {
            "kind": "weighted_periodic_hnf_quotient",
            "certified": True,
            "can_tile": True,
            "model": certificate["model"],
            "copies": certificate["copies"] * 8,
            "determinant": certificate["determinant"] * 8,
            "period_vectors": [[2 * coordinate for coordinate in vector] for vector in basis],
            "placements": placements,
        }
        replay = backend.replay_certificate(
            backend.orientations(backend.record_occupancy(row)), doubled
        )
        assert replay["verified"] is True
        results.append({
            "id": row["id"],
            "classification": "periodic_quotient_cluster_substitution",
            "substitution": {
                "certified": True,
                "inflation": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
                "parent_metatile_copies": certificate["copies"],
                "child_metatile_copies": 8,
                "expanded_tile_copies": len(placements),
                "parent_period_vectors": basis,
                "expanded_period_vectors": doubled["period_vectors"],
                "child_clusters": child_clusters,
                "replay": replay,
                "interpretation": "The eight-tile periodic quotient is the metatile; its scale-two image is exactly eight translated copies of that quotient metatile.",
            },
        })
    assert len(results) == args.expected_rules
    with gzip.open(output_path, "wt", encoding="utf8", compresslevel=9) as target:
        for result in results:
            target.write(json.dumps(result, separators=(",", ":")) + "\n")
    try:
        output_label = str(output_path.relative_to(ROOT))
    except ValueError:
        output_label = str(output_path)
    print(json.dumps({"output": output_label, "rules": [r["id"] for r in results]}))


if __name__ == "__main__":
    main()
