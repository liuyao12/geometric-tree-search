#!/usr/bin/env python3
"""Focused invariance and incidence tests for the shared macro graph."""

from __future__ import annotations

import math

from materials_gcts_port_incidence_graph import (
    canonical_port_incidence_graph)


STATE = {
    "parent": {"species": "X", "radial_counts": (1, 2)},
    "source": {"species": "Y", "radial_counts": (2, 3)},
    "separation_bin": 4,
}


def _witness(parent, source):
    return {"state": STATE, "parent_position": parent,
            "parent_species": "X", "source_position": source,
            "source_species": "Y"}


def _actions():
    return (
        {"point": (1., 0., 0.), "species": "X",
         "port_witnesses": (_witness((0., 0., 0.), (0., 1., 0.)),)},
        {"point": (0., 2., 0.), "species": "Y",
         "port_witnesses": (_witness((0., 1., 0.), (0., 2., 1.)),)},
        {"point": (0., 0., 3.), "species": "X",
         "port_witnesses": (_witness((0., 2., 1.), (1., 2., 1.)),)},
    )


def _transform(point):
    # Proper 90-degree z rotation followed by translation.
    x, y, z = point
    return (7. - y, -3. + x, 11. + z)


def test_permutation_and_proper_motion_invariance():
    actions = _actions()
    base = canonical_port_incidence_graph((0., 0., 0.), actions, 1.)
    transformed = tuple({
        "point": _transform(action["point"]),
        "species": action["species"],
        "port_witnesses": tuple({
            **witness,
            "parent_position": _transform(witness["parent_position"]),
            "source_position": _transform(witness["source_position"]),
        } for witness in action["port_witnesses"]),
    } for action in reversed(actions))
    moved = canonical_port_incidence_graph(
        _transform((0., 0., 0.)), transformed, 1.)
    assert base == moved
    assert not base["raw_occurrence_ids_serialized"]
    assert not base["global_frame_semantic"]


def test_port_incidence_and_chirality_are_retained():
    graph = canonical_port_incidence_graph((0., 0., 0.), _actions(), 1.)
    relations = {name for edge in graph["edges"]
                 for row in edge["port_pair_relations"]
                 for name in row["relations"]}
    assert "left_source_is_right_parent" in relations or \
        "right_source_is_left_parent" in relations
    mirrored = []
    for action in _actions():
        mirror = lambda p: (-p[0], p[1], p[2])
        mirrored.append({
            "point": mirror(action["point"]), "species": action["species"],
            "port_witnesses": tuple({
                **witness,
                "parent_position": mirror(witness["parent_position"]),
                "source_position": mirror(witness["source_position"]),
            } for witness in action["port_witnesses"]),
        })
    reflected = canonical_port_incidence_graph(
        (0., 0., 0.), mirrored, 1.)
    assert graph["canonical_digest"] != reflected["canonical_digest"]


def test_rejects_missing_ports_and_degenerate_geometry():
    actions = list(_actions())
    actions[0] = {**actions[0], "port_witnesses": ()}
    try:
        canonical_port_incidence_graph((0., 0., 0.), actions, 1.)
    except ValueError:
        pass
    else:
        raise AssertionError("missing witnessed port accepted")
    collinear = tuple({**action, "point": (float(index), 0., 0.)}
                      for index, action in enumerate(_actions()))
    try:
        canonical_port_incidence_graph((0., 0., 0.), collinear, 1.)
    except ValueError:
        pass
    else:
        raise AssertionError("continuous-frame macro accepted")


if __name__ == "__main__":
    test_permutation_and_proper_motion_invariance()
    test_port_incidence_and_chirality_are_retained()
    test_rejects_missing_ports_and_degenerate_geometry()
    print("port incidence graph tests passed")
