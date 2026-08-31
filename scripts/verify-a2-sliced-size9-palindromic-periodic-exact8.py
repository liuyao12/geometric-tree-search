#!/usr/bin/env python3
"""Independently replay the complete recovered size-nine eight-copy campaign."""

from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/a2-sliced-size9-palindromic-periodic-exact8-complete.ndjson.gz"
SUBSTITUTIONS = ROOT / "data/a2-sliced-size9-palindromic-periodic-cluster-substitutions.ndjson.gz"
BACKEND = ROOT / "scripts/screen-a2-layered-periodic-z3.py"


def load_backend():
    spec = importlib.util.spec_from_file_location("a2_periodic_backend", BACKEND)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    backend = load_backend()
    with gzip.open(REPORT, "rt", encoding="utf8") as source:
        rows = [json.loads(line) for line in source if line.strip()]
    assert len(rows) == 8
    positives = []
    negatives = []
    for row in rows:
        result = row["periodic_z3"]
        assert result["solver_unknown"] == 0
        assert result["hnf_total"] == 455
        assert result["hnf_orbit_total"] == 104
        if row["classification"] == "periodic":
            certificate = result["certificate"]
            replay = backend.replay_certificate(
                backend.orientations(backend.record_occupancy(row)), certificate
            )
            assert certificate["copies"] == 8
            assert certificate["determinant"] == 12
            assert replay["verified"] is True
            positives.append(row["id"])
            continue
        assert row["classification"] == "unresolved"
        assert result["hnf_range_exhausted"] is True
        assert result["hnf_visited"] == 104
        assert result["hnf_covered"] == 455
        assert result["exhausted_by_copies"] == {"8": 455}
        receipts = result["orbit_shard_receipts"]
        assert len(receipts) == 104
        assert [receipt["orbit_range"] for receipt in receipts] == [
            [index, index + 1] for index in range(104)
        ]
        assert sum(receipt["hnfs_covered"] for receipt in receipts) == 455
        negatives.append(row["id"])
    assert sorted(positives) == ["a2sp_9_15353", "a2sp_9_17745"]
    assert len(negatives) == 6
    rows_by_id = {row["id"]: row for row in rows}
    with gzip.open(SUBSTITUTIONS, "rt", encoding="utf8") as source:
        substitutions = [json.loads(line) for line in source if line.strip()]
    assert sorted(rule["id"] for rule in substitutions) == sorted(positives)
    for rule in substitutions:
        substitution = rule["substitution"]
        assert substitution["certified"] is True
        assert substitution["inflation"] == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
        assert substitution["parent_metatile_copies"] == 8
        assert substitution["child_metatile_copies"] == 8
        assert len(substitution["child_clusters"]) == 8
        placements = [
            placement
            for cluster in substitution["child_clusters"]
            for placement in cluster["placements"]
        ]
        assert len(placements) == substitution["expanded_tile_copies"] == 64
        expanded_certificate = {
            "determinant": 96,
            "period_vectors": substitution["expanded_period_vectors"],
            "placements": placements,
        }
        replay = backend.replay_certificate(
            backend.orientations(backend.record_occupancy(rows_by_id[rule["id"]])),
            expanded_certificate,
        )
        assert replay["verified"] is True
    print(json.dumps({
        "rows": len(rows), "periodic": positives, "exact_negative": negatives,
        "cluster_substitutions": len(substitutions),
    }))


if __name__ == "__main__":
    main()
