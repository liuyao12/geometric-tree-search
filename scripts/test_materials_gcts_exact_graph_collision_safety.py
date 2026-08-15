#!/usr/bin/env python3
"""Adversarial exact-isomorphism checks behind the WL bucket."""

from materials_gcts_port_graph_macros import (
    _GraphCandidate, _canonical_graph_orders, _first_exact_isomorphism)


label = (0, 0, (1, 2, 3))


def bidirectional(pairs):
    return tuple(item for left, right in pairs
                 for item in ((left, right, label), (right, left, label)))


# Force the same refinement color/bucket to model a hash/WL collision.  The
# exact checker must still reject rooted path P4 versus rooted star K1,3.
path = _GraphCandidate(
    0, frozenset(range(4)), tuple((node, "collision") for node in range(4)),
    ("forged-collision",), (0, 1, 2, 3))
star = _GraphCandidate(
    4, frozenset(range(4, 8)),
    tuple((node, "collision") for node in range(4, 8)),
    ("forged-collision",), (4, 5, 6, 7))
edges = bidirectional(((0, 1), (1, 2), (2, 3),
                       (4, 5), (4, 6), (4, 7)))
types = {node: 0 for node in range(8)}
assert _first_exact_isomorphism(path, star, types, edges) is None

# A permuted copy of the path is accepted, and its exact canonical code agrees.
copy = _GraphCandidate(
    8, frozenset(range(8, 12)),
    tuple((node, "collision") for node in range(8, 12)),
    ("forged-collision",), (8, 9, 10, 11))
copy_edges = edges + bidirectional(((8, 10), (10, 11), (11, 9)))
types.update({node: 0 for node in range(8, 12)})
mapping = _first_exact_isomorphism(copy, path, types, copy_edges)
assert mapping is not None
path_code, _ = _canonical_graph_orders(path, types, copy_edges)
copy_code, _ = _canonical_graph_orders(copy, types, copy_edges)
assert path_code == copy_code

print("exact graph canonicalization rejects adversarial WL collisions")
