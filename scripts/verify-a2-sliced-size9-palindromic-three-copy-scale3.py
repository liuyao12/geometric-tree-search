#!/usr/bin/env python3
"""Re-enumerate and replay the 04636 three-copy scale-3 exclusions."""

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
    False: {
        "raw": 370,
        "parents": 67,
        "digest": "42c71561f42e3e15ee1f1967203dd7f36f13e1e8041d32c8c616835539c78e5e",
    },
    True: {
        "raw": 3796,
        "parents": 455,
        "digest": "c2699dbffde5b875a66163942502cfa5e309d9b1d78245bffb73309aa3c4af3c",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" /
                    "a2-sliced-size9-palindromic-exact6-reflection-representatives.ndjson.gz"),
    )
    parser.add_argument(
        "--archive",
        default=str(ROOT / "data" /
                    "a2-sliced-size9-palindromic-three-copy-substitution-scale3-04636.ndjson.gz"),
    )
    args = parser.parse_args()

    source = next(record for record in TWO.read_ndjson(Path(args.input))
                  if record["id"] == "a2sp_9_04636")
    with gzip.open(args.archive, "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    if len(records) != 2:
        raise AssertionError("scale-3 archive must contain proper and reflected records")

    totals = {"parents": 0, "replayed": 0}
    for reflected, record in zip((False, True), records):
        expected = EXPECTED[reflected]
        detail = record["three_copy_alcove_metatile_screen"]
        enumerated = THREE.enumerate_three_copy_metatiles(source, reflected)
        if (record["id"] != "a2sp_9_04636"
                or record["classification"]
                != "no_three_copy_metatile_scalar3_substitution"
                or detail["certified"] is not True
                or detail["scale"] != 3
                or detail["include_reflections"] is not reflected
                or detail["raw_connected_extensions"] != expected["raw"]
                or detail["symmetry_distinct_metatiles"] != expected["parents"]
                or detail["canonical_sha256"] != expected["digest"]
                or enumerated["raw_connected_extensions"] != expected["raw"]
                or enumerated["symmetry_distinct_metatiles"] != expected["parents"]
                or enumerated["canonical_sha256"] != expected["digest"]
                or detail["parent_range"] != [0, expected["parents"]]
                or detail["parents_completed"] != expected["parents"]
                or detail["parent_counts"] != {
                    "atomic_local_obstruction": expected["parents"],
                    "local_obstruction": 0,
                    "exact_unsat": 0,
                    "mixed_metatile_rule": 0,
                    "unresolved": 0,
                }):
            raise AssertionError(f"scale-3 receipt identity mismatch: reflected={reflected}")
        alphabet = TWO.oriented_alphabet([{"alcoves": source["alcoves"]}], reflected)
        results = detail["parent_results"]
        if len(results) != expected["parents"]:
            raise AssertionError("parent receipt count mismatch")
        for index, result in enumerate(results):
            if (result["parent_index"] != index
                    or result["classification"] != "atomic_local_obstruction"):
                raise AssertionError(f"unexpected parent result at {index}")
            parent = enumerated["metatiles"][index]
            target = SUB.inflated_cells(parent["alcoves"], 3)
            target_cell = tuple(result["atomic_local_obstruction_replay"]
                                ["uncovered_alcove"])
            replay = TWO.replay_local_obstruction(target, alphabet, target_cell)
            if replay != result["atomic_local_obstruction_replay"]:
                raise AssertionError(f"local obstruction replay mismatch at {index}")
            totals["replayed"] += 1
        totals["parents"] += expected["parents"]

    print(json.dumps({
        "id": "a2sp_9_04636",
        "models": ["proper", "reflected"],
        **totals,
    }, indent=2))


if __name__ == "__main__":
    main()
