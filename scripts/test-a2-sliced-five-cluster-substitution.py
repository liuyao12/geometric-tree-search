#!/usr/bin/env python3
"""Regression checks for the complete five-copy A2 metatile census."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIVE = load("a2_sliced_five_cluster", "screen-a2-sliced-five-cluster-substitution.py")
FOUR = FIVE.FOUR
TWO = FIVE.TWO


def main():
    # A single Kuhn alcove keeps the independent census small while exercising
    # every extension/canonicalization/replay path used by the long campaign.
    record = {
        "id": "five_copy_test_alcove",
        "alcoves": [{"base": [0, 0, 0], "order": [0, 1, 2]}],
    }
    four = FOUR.enumerate_four_copy_metatiles(record, False)
    with tempfile.TemporaryDirectory() as directory:
        cache = Path(directory) / "four-copy.json"
        cache.write_text(json.dumps({
            "id": record["id"],
            "include_reflections": False,
            "copies": 4,
            "enumerated": four,
        }, separators=(",", ":")))
        five = FIVE.enumerate_five_copy_metatiles(record, cache, False)

    keys = [tuple(tuple(cell) for cell in item["canonical_key"])
            for item in five["metatiles"]]
    assert keys == sorted(set(keys))
    assert five["four_copy_parent_total"] == len(four["metatiles"])
    assert five["symmetry_distinct_metatiles"] == len(keys) > 0
    assert all(len(item["alcoves"]) == 5 for item in five["metatiles"])
    assert all(item["base_decomposition"]["replay"]["verified"]
               for item in five["metatiles"])

    # Independently reconstruct the canonical extension set from the complete
    # four-copy census.  This guards against accidentally skipping a parent,
    # orientation, boundary face, or translation in the production routine.
    orientations = FIVE.SUB.oriented_cells(record["alcoves"], False)
    expected = set()
    for parent in four["metatiles"]:
        cluster = parent["alcoves"]
        occupied = {FIVE.SUB.cell_key(cell) for cell in cluster}
        for neighbor in TWO.adjacent_atomic_cells(cluster):
            neighbor_key = FIVE.SUB.cell_key(neighbor)
            for orientation in orientations:
                for own_cell in orientation["cells"]:
                    own_key = FIVE.SUB.cell_key(own_cell)
                    if own_key[3] != neighbor_key[3]:
                        continue
                    delta = tuple(neighbor_key[axis] - own_key[axis]
                                  for axis in range(3))
                    partner = TWO.translated_cells(orientation["cells"], delta)
                    if occupied.intersection(FIVE.SUB.cell_key(cell)
                                             for cell in partner):
                        continue
                    expected.add(TWO.canonical_key([*cluster, *partner], False))
    assert set(keys) == expected
    print(json.dumps({
        "four_copy_metatiles": len(four["metatiles"]),
        "five_copy_metatiles": len(keys),
        "canonical_sha256": five["canonical_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
