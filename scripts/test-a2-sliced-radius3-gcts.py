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

# A one-node slice stops before the first branch, and the next slice must
# resume that exact stack instead of reconstructing or skipping it.
original_extension_universe = module.CORE.extension_universe
module.CORE.extension_universe = lambda root, orientations, selected: [
    {
        "orientation_index": 0,
        "translation": [1, 0, 0],
        "occupancy": {(0, 0, 0): 1, (1, 0, 0): 1},
    },
    {
        "orientation_index": 0,
        "translation": [2, 0, 0],
        "occupancy": {(0, 0, 0): 1},
    },
]
first_slice = module.exact_patch_extension(
    {(0, 0, 0): 47}, [], [], timeout_ms=1000, max_nodes=1
)
assert first_slice["result"] == "unknown"
assert first_slice["checkpoint"]["nodes"] == 1
second_slice = module.exact_patch_extension(
    {(0, 0, 0): 47}, [], [], timeout_ms=1000, max_nodes=1,
    resume=first_slice["checkpoint"],
)
assert second_slice["result"] == "sat"
assert second_slice["nodes"] == 2
module.CORE.extension_universe = original_extension_universe

print("A2-sliced radius-three GCTS structural regression passed")
