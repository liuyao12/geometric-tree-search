#!/usr/bin/env python3
"""Re-enumerate and replay scale-3 screens for the additional size-9 leaders."""

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
    ("a2sp_9_01085", False): (906, 123,
        "8df10a8518cd8ccfc31fdbd095d350a513b67e8ee19844e9cff80525d75da49e"),
    ("a2sp_9_01085", True): (3214, 483,
        "60d842bdb7914b7ac5975d308a1ec5b61bb9a68462609cbc6505b56938b9e1e0"),
    ("a2sp_9_04468", False): (2982, 937,
        "cb2cff6140090b86061663036ca99e94c17ae01d79365d0becd0de79d307a13c"),
    ("a2sp_9_04468", True): (12462, 3581,
        "5919bab70ce19f8a9d4e37a33d54ce516f12ae2cd2793df276c0a1e733a0630b"),
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
                    "a2-sliced-size9-palindromic-three-copy-substitution-scale3-additional-leaders.ndjson.gz"),
    )
    args = parser.parse_args()

    sources = {record["id"]: record for record in TWO.read_ndjson(Path(args.input))}
    with gzip.open(args.archive, "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    if len(records) != len(EXPECTED):
        raise AssertionError("additional scale-3 archive has the wrong record count")
    seen = set()
    replayed = 0
    for record in records:
        detail = record["three_copy_alcove_metatile_screen"]
        identity = (record["id"], detail["include_reflections"])
        if identity not in EXPECTED or identity in seen:
            raise AssertionError(f"unexpected scale-3 identity: {identity}")
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
                or detail["parent_counts"] != {
                    "atomic_local_obstruction": parents,
                    "local_obstruction": 0,
                    "exact_unsat": 0,
                    "mixed_metatile_rule": 0,
                    "unresolved": 0,
                }):
            raise AssertionError(f"scale-3 receipt mismatch: {identity}")
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
    if seen != set(EXPECTED):
        raise AssertionError("scale-3 archive is incomplete")
    print(json.dumps({
        "candidates": 2,
        "models": 4,
        "parents_replayed": replayed,
        "replay_failures": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
