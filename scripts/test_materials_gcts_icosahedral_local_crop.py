#!/usr/bin/env python3
"""Exactness and equivariance checks for local 6D oracle crops."""

from __future__ import annotations

import math

from materials_gcts_icosahedral_modelset import (
    oracle_crop_fast, oracle_patch_fast)


def _colored(configuration):
    return sorted((tuple(round(value, 10) for value in point), color)
                  for point, color in zip(
                      configuration.positions, configuration.species))


def test_local_crop_matches_a_sufficient_global_lift_cube():
    center = (5.25, -3.75, 4.5)
    radius = 5.25
    local, local_lifts = oracle_crop_fast(center, radius)
    global_cloud, global_lifts = oracle_patch_fast(
        12, math.dist((0., 0., 0.), center) + radius)
    selected = [(point, color, lift) for point, color, lift in zip(
        global_cloud.positions, global_cloud.species, global_lifts)
        if math.dist(point, center) <= radius + 1e-10]
    assert _colored(local) == sorted(
        (tuple(round(value, 10) for value in point), color)
        for point, color, _lift in selected)
    assert set(local_lifts) == {lift for _point, _color, lift in selected}


def test_far_crop_is_finite_deterministic_and_needs_no_global_bound():
    first, first_lifts = oracle_crop_fast((0., -120., -160.), 9.)
    second, second_lifts = oracle_crop_fast((0., -120., -160.), 9.)
    assert len(first.positions) == 480
    assert first.positions == second.positions
    assert first.species == second.species
    assert first_lifts == second_lifts
    assert all(math.dist(point, (0., -120., -160.)) <= 9. + 1e-10
               for point in first.positions)


def test_bad_local_crop_inputs_fail_closed():
    for center, radius in [((0., 0.), 1.), ((0., 0., float("nan")), 1.),
                           ((0., 0., 0.), 0.)]:
        try:
            oracle_crop_fast(center, radius)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid local crop input was accepted")


if __name__ == "__main__":
    test_local_crop_matches_a_sufficient_global_lift_cube()
    test_far_crop_is_finite_deterministic_and_needs_no_global_bound()
    test_bad_local_crop_inputs_fail_closed()
    print("local 6D IQC crop: passed")
