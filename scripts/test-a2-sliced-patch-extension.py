#!/usr/bin/env python3
"""Regression checks for generic replayed-patch extension."""

from __future__ import annotations

import importlib.util
import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "a2_patch_extension", ROOT / "scripts" / "screen-a2-sliced-patch-extension.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

first = [{"orientation_index": 0, "translation": [0, 0, 0]}]
added = [{"orientation_index": 2, "translation": [1, 0, 0]}]
retained = {
    "id": "retained",
    "retained_corona_extension_classification": "radius2_witness",
    "retained_corona_extension": {
        "first_patch": first,
        "added_patch": added,
        "replay": {"verified": True},
    },
}
assert module.source_patch(retained) == (2, first + added, "retained_corona_extension")

cegar = {
    "id": "cegar",
    "corona2_classification": "radius2_witness",
    "corona2_cegar": {
        "first_patch": first,
        "added_patch": added,
        "replay": {"verified": True},
    },
}
assert module.source_patch(cegar) == (2, first + added, "corona2_cegar")

chained = {
    "id": "chained",
    "patch_extension_classification": "radius3_witness",
    "patch_extension": {
        "target_radius": 3,
        "source_patch": first,
        "added_patch": added,
        "replay": {"verified": True},
    },
}
assert module.source_patch(chained) == (3, first + added, "patch_extension")

with gzip.open(
    ROOT / "data" / "a2-sliced-alcove-size7-leads-radius2-radius3-gcts.ndjson.gz",
    "rt",
) as stream:
    leads = [json.loads(line) for line in stream if line.strip()]
assert len(leads) == 8
assert len({record["id"] for record in leads}) == 8
for record in leads:
    root = module.GEOMETRY.record_occupancy(record)
    orientations = module.GEOMETRY.orientations(root)
    if record.get("retained_corona_extension_classification") == "radius2_witness":
        receipt = record["retained_corona_extension"]
    else:
        assert record["corona2_classification"] == "radius2_witness"
        receipt = record["corona2_cegar"]
    replay = module.CEGAR.replay_extension(
        orientations, receipt["first_patch"], receipt["added_patch"]
    )
    assert replay["verified"]
    assert replay == receipt["replay"]
    assert record["radius3_gcts_classification"] == "unresolved"

assert sum(len(record["radius3_gcts"]["radius2_failure_clauses"])
           for record in leads) == 759
assert sum(len(record["radius3_gcts"]["first_corona_failure_clauses"])
           for record in leads) == 731

print("A2-sliced generic patch-extension regression passed")
