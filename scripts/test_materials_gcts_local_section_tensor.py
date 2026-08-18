#!/usr/bin/env python3

import itertools
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


def test_explicit_chirality_channel_is_proper_invariant_and_mirror_odd():
    schema = LocalSectionSchema(("X",), 1., angular_cutoff=4.,
                                include_chirality=True)
    action = ((0., 0., 0.),)
    occupied = ((1., 0., 0.), (0., 2., 0.), (0., 0., 3.))
    source = local_section_tensor(
        action, ("X",), occupied, ("X",) * 3, schema)
    proper = local_section_tensor(
        tuple(_transform(point) for point in action), ("X",),
        tuple(_transform(point) for point in occupied), ("X",) * 3,
        schema)
    mirror = local_section_tensor(
        tuple((-point[0], point[1], point[2]) for point in action), ("X",),
        tuple((-point[0], point[1], point[2]) for point in occupied),
        ("X",) * 3, schema)
    assert source.chirality_preserved
    assert len(source.values) == len(local_section_feature_names(schema)) == 15
    assert all(abs(left - right) < 1e-12
               for left, right in zip(source.values, proper.values))
    assert abs(source.values[-1]) > 1e-6
    brute = 0.
    for first, second, third in itertools.permutations(occupied, 3):
        radii = tuple(math.sqrt(sum(value * value for value in point))
                      for point in (first, second, third))
        unit = tuple(tuple(value / radius for value in point)
                     for point, radius in zip((first, second, third), radii))
        determinant = (unit[0][0] * (unit[1][1] * unit[2][2] -
                       unit[1][2] * unit[2][1]) - unit[0][1] *
                       (unit[1][0] * unit[2][2] - unit[1][2] * unit[2][0]) +
                       unit[0][2] * (unit[1][0] * unit[2][1] -
                       unit[1][1] * unit[2][0]))
        brute += determinant * (radii[1] / 4.) * (radii[2] / 4.) ** 2
    assert abs(source.values[-1] - brute) < 1e-12
    assert abs(source.values[-1] + mirror.values[-1]) < 1e-12
    assert source.values[:-1] == mirror.values[:-1]


if __name__ == "__main__":
    test_local_section_is_permutation_and_proper_se3_invariant()
    test_local_section_rejects_tainted_or_invalid_inputs()
    test_explicit_chirality_channel_is_proper_invariant_and_mirror_odd()
    print("local-section tensor tests passed")
