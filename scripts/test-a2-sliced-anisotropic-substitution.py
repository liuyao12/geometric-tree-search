#!/usr/bin/env python3
"""Structural checks for the A2-sliced pI+cJ substitution model."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "a2_sliced_anisotropic",
    ROOT / "scripts" / "screen-a2-sliced-anisotropic-substitution.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

record = json.loads((ROOT / "data" /
    "a2-sliced-alcove-size8-directed-exact6-reflection-representatives.ndjson"
).read_text().splitlines()[1])

scalar = MODULE.inflated_cells(record["alcoves"], 2, 2)
reference = MODULE.SUB.inflated_cells(record["alcoves"], 2)
assert scalar == reference

assert MODULE.noncellular_boundary_witness(record["alcoves"], 2, 2) is None
anisotropic = MODULE.screen(record, 2, 5, 1000)
assert anisotropic["anisotropic_substitution_classification"] \
    == "inflation_not_alcove_cellular"
assert anisotropic["anisotropic_substitution"]["certified"]
assert anisotropic["anisotropic_substitution"]["noncellular_substitution_open"]

try:
    MODULE.inflated_cells(record["alcoves"], 2, 3)
    raise AssertionError("nonintegral layer congruence must be rejected")
except ValueError:
    pass

print("A2-sliced anisotropic substitution structural regression passed")
