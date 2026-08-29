#!/usr/bin/env python3
"""Regression checks for generic replayed-patch extension."""

from __future__ import annotations

import importlib.util
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

print("A2-sliced generic patch-extension regression passed")
