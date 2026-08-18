#!/usr/bin/env python3

import math

from materials_gcts_local_section_tensor import (
    LocalSectionSchema, local_section_feature_names, local_section_tensor)


def _transform(point):
    # Proper signed permutation, determinant +1, followed by translation.
    return (point[1] + 7., point[0] - 3., -point[2] + 2.)


def test_local_section_is_permutation_and_proper_se3_invariant():
    schema = LocalSectionSchema(("X", "Y", "Z"), 1.)
    actions = ((.2, .1, .3), (1.3, -.2, .7), (-.4, 1.1, .5))
    action_colors = ("X", "Y", "X")
    occupied = ((0., 0., 0.), (1., 1., 0.), (-1., .5, 1.),
                (.7, -1.2, .4), (2., .3, -1.))
    colors = ("X", "Y", "Z", "X", "Z")
    source = local_section_tensor(
        actions, action_colors, occupied, colors, schema)
    transformed = local_section_tensor(
        tuple(_transform(point) for point in reversed(actions)),
        tuple(reversed(action_colors)),
        tuple(_transform(point) for point in reversed(occupied)),
        tuple(reversed(colors)), schema)
    reflected = local_section_tensor(
        tuple((-point[0], point[1], point[2]) for point in actions),
        action_colors,
        tuple((-point[0], point[1], point[2]) for point in occupied),
        colors, schema)
    assert source.values == transformed.values
    assert source.values == reflected.values
    assert source.schema_digest == transformed.schema_digest
    assert source.proper_se3_invariant
    assert not source.lattice_coordinates_used
    assert not source.target_used
    assert not source.chirality_preserved
    assert len(source.values) == len(local_section_feature_names(schema)) == 180


def test_local_section_rejects_tainted_or_invalid_inputs():
    try:
        LocalSectionSchema(("X",), 1., target_used=True)
        local_section_feature_names(LocalSectionSchema(
            ("X",), 1., target_used=True))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted schema was accepted")
    schema = LocalSectionSchema(("X",), 1.)
    for actions, occupied in ((((0., 0., 0.),), ((0., 0., 0.),)),
                              (((math.nan, 0., 0.),), ())):
        try:
            local_section_tensor(actions, ("X",), occupied,
                                 ("X",) if occupied else (), schema)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid section geometry was accepted")


if __name__ == "__main__":
    test_local_section_is_permutation_and_proper_se3_invariant()
    test_local_section_rejects_tainted_or_invalid_inputs()
    print("local-section tensor tests passed")
