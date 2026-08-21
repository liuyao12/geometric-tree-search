#!/usr/bin/env python3
"""Contract tests for the geometry-complete recurrent IQC macro corpus."""

from __future__ import annotations

import math

from materials_gcts_iqc_recurrent_macro_geometry_dataset import (
    DEVELOPMENT_CENTERS, SEARCH_DEPTH, _canonical_macro_geometry,
    _domain_audit, load_fixture, validate_dataset)


def _witness(parent, source):
    return ({
        "state": {
            "parent": {"species": "X", "radial_counts": (1, 2)},
            "source": {"species": "Y", "radial_counts": (2, 3)},
            "separation_bin": 4,
        },
        "parent_position": parent,
        "parent_species": "X",
        "source_position": source,
        "source_species": "Y",
    },)


def _rotate(point):
    # Proper signed-coordinate rotation: (x,y,z) -> (-y,x,z).
    return (-point[1] + 7., point[0] - 3., point[2] + 5.)


def test_canonical_macro_geometry_is_proper_motion_and_order_invariant():
    center = (0., 0., 0.)
    actions = (((1., 0., 0.), "X"), ((0., 2., 0.), "Y"),
               ((0., 0., 3.), "Z"))
    witnesses = (_witness((0., 0., 0.), (.5, 0., 0.)),
                 _witness((0., 0., 0.), (0., 1., 0.)),
                 _witness((0., 0., 0.), (0., 0., 1.5)))
    first = _canonical_macro_geometry(center, actions, witnesses, 1.)
    order = (2, 0, 1)
    transformed_actions = tuple((_rotate(actions[index][0]),
                                 actions[index][1]) for index in order)
    transformed_witnesses = tuple(tuple({
        **row,
        "parent_position": _rotate(row["parent_position"]),
        "source_position": _rotate(row["source_position"]),
    } for row in witnesses[index]) for index in order)
    second = _canonical_macro_geometry(
        _rotate(center), transformed_actions, transformed_witnesses, 1.)
    assert first == second
    assert first["proper_frame_determinant"] == 1
    assert len(first["nodes"]) == SEARCH_DEPTH


def test_declared_domains_are_disjoint():
    pairwise, required, wide = _domain_audit()
    assert len(DEVELOPMENT_CENTERS) == 17
    assert pairwise > 0
    assert wide > required
    assert math.isfinite(pairwise)


def test_frozen_fixture_contract():
    payload = load_fixture()
    assert validate_dataset(payload)
    assert len(payload["groups"]) == 17
    assert payload["upstream_fit_groups"] == 17
    assert payload["upstream_heldout_groups"] == 0
    assert not payload["wide_atoms_or_labels_used"]
    assert not payload["raw_occurrence_ids_serialized"]


if __name__ == "__main__":
    test_canonical_macro_geometry_is_proper_motion_and_order_invariant()
    test_declared_domains_are_disjoint()
    test_frozen_fixture_contract()
    print("recurrent macro geometry dataset tests passed")
