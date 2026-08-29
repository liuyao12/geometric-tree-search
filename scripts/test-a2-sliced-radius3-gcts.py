#!/usr/bin/env python3
"""Small structural checks for hierarchical A2 radius-three GCTS."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "a2_radius3_gcts", ROOT / "scripts" / "screen-a2-sliced-radius3-gcts.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

placement = {"orientation_index": 2, "translation": [1, -1, 0]}
assert module.key(placement) == (2, (1, -1, 0))
assert module.clause_signature([module.key(placement), module.key(placement)]) == (
    (2, (1, -1, 0)),
)
assert module.serialized_clause([module.key(placement)]) == [placement]
assert module.decoded_clauses([[placement]]) == [((2, (1, -1, 0)),)]

trivial = module.exact_patch_extension(
    {(0, 0, 0): 48},
    [{"occupancy": {(0, 0, 0): 48}}],
    [],
    timeout_ms=100,
    max_nodes=100,
)
assert trivial["result"] == "sat"
assert trivial["added"] == []

print("A2-sliced radius-three GCTS structural regression passed")
