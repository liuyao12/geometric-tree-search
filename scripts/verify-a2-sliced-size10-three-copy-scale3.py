#!/usr/bin/env python3
"""Re-enumerate and replay the size-10 leader scale-3 exclusions."""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_three_cluster",
    ROOT / "scripts" / "screen-a2-sliced-three-cluster-substitution.py",
)
THREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(THREE)
TWO = THREE.TWO
SUB = THREE.SUB

EXPECTED = {
    ("a2sa_10_35323", False): (3737, 1447,
        "a4ffe6273910fc1db16f4a587b0fca7a98f87b7e26a43d40ae07f12f303a4468"),
    ("a2sa_10_35323", True): (16411, 4250,
        "1fdaf898445b8e51aacd2a9b8b070fb1789b4596a90911b190e891dd8491a870"),
    ("a2sa_10_36141", False): (3595, 1298,
        "82273709353cce7d3a4d8c59f7fb51e36a9193184476cf6f1a291c548dc467a2"),
    ("a2sa_10_36141", True): (16332, 4057,
        "bf23b36ee020a70e2789ad1568ebe84cca2f738cb0a89e721608b416d1255743"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" /
                    "a2-sliced-size10-focused-periodic-exact6-ranks9-72.ndjson.gz"),
    )
    parser.add_argument(
        "--archive",
        default=str(ROOT / "data" /
                    "a2-sliced-size10-three-copy-substitution-scale3-leaders.ndjson.gz"),
    )
    args = parser.parse_args()
    sources = {record["id"]: record for record in TWO.read_ndjson(Path(args.input))}
    with gzip.open(args.archive, "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    if len(records) != len(EXPECTED):
        raise AssertionError("size-10 scale-3 archive has the wrong record count")
    seen = set()
    replayed = 0
    for record in records:
        detail = record["three_copy_alcove_metatile_screen"]
        identity = (record["id"], detail["include_reflections"])
        if identity not in EXPECTED or identity in seen:
            raise AssertionError(f"unexpected size-10 scale-3 identity: {identity}")
        seen.add(identity)
        raw, parents, digest = EXPECTED[identity]
        source = sources[record["id"]]
        enumerated = THREE.enumerate_three_copy_metatiles(source, identity[1])
        if (record["classification"]
                != "no_three_copy_metatile_scalar3_substitution"
                or detail["certified"] is not True
                or detail["scale"] != 3
                or detail["raw_connected_extensions"] != raw
                or detail["symmetry_distinct_metatiles"] != parents
                or detail["canonical_sha256"] != digest
                or enumerated["raw_connected_extensions"] != raw
                or enumerated["symmetry_distinct_metatiles"] != parents
                or enumerated["canonical_sha256"] != digest
                or detail["parents_completed"] != parents
                or detail["parent_counts"]["atomic_local_obstruction"] != parents
                or any(detail["parent_counts"][kind] for kind in
                       ("local_obstruction", "exact_unsat", "mixed_metatile_rule", "unresolved"))):
            raise AssertionError(f"size-10 scale-3 receipt mismatch: {identity}")
        alphabet = TWO.oriented_alphabet([{"alcoves": source["alcoves"]}], identity[1])
        for index, result in enumerate(detail["parent_results"]):
            target = SUB.inflated_cells(enumerated["metatiles"][index]["alcoves"], 3)
            target_cell = tuple(result["atomic_local_obstruction_replay"]
                                ["uncovered_alcove"])
            replay = TWO.replay_local_obstruction(target, alphabet, target_cell)
            if (result["parent_index"] != index
                    or result["classification"] != "atomic_local_obstruction"
                    or replay != result["atomic_local_obstruction_replay"]):
                raise AssertionError(f"obstruction replay mismatch: {identity} parent {index}")
            replayed += 1
    print(json.dumps({
        "candidates": 2,
        "models": 4,
        "parents_replayed": replayed,
        "replay_failures": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
