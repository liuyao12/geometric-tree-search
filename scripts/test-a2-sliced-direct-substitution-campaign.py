#!/usr/bin/env python3
"""Unit checks for the resumable direct-substitution campaign."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_direct_campaign",
    ROOT / "scripts" / "run-a2-sliced-direct-substitution-campaign.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

assert MODULE.parse_scales("2,4-6,3") == [2, 3, 4, 5, 6]
assert MODULE.valid_result({
    "id": "negative",
    "alcove_substitution_classification": "no_direct_scalar_substitution",
    "alcove_substitution": {
        "scale": 2,
        "include_reflections": False,
        "certified": True,
        "atomic_uncovered_alcove": [0, 0, 0, "012"],
        "independent_replay": {"verified": True},
    },
})
assert not MODULE.valid_result({
    "id": "bad-negative",
    "alcove_substitution_classification": "no_direct_scalar_substitution",
    "alcove_substitution": {
        "scale": 2,
        "include_reflections": False,
        "certified": True,
        "atomic_uncovered_alcove": [0, 0, 0, "012"],
    },
})
assert MODULE.valid_result({
    "id": "positive",
    "alcove_substitution_classification": "substitution_rule",
    "alcove_substitution": {
        "scale": 2,
        "include_reflections": True,
        "replay": {"verified": True},
    },
})

print("A2-sliced direct-substitution campaign regression passed")
