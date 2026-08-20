#!/usr/bin/env python3
"""Regression and invariance controls for the IQC macro dataset."""

import math

from materials_gcts_iqc_parent_child_macro_dataset import (
    load_default_result, macro_features)


def test_parent_child_macro_dataset():
    row = load_default_result()
    assert row["development_groups"] == 10
    assert row["examples"] == 1278
    assert row["exact_examples"] == 142
    assert row["feature_count"] == 62
    assert row["target_used_for_geometry"] is False
    assert row["proper_se3_invariant"] is True
    assert row["permutation_invariant_within_blocks"] is True


def test_macro_feature_rigid_and_permutation_invariance():
    parent = (((0., 0., 0.), "X"), ((1., 0., 0.), "Y"),
              ((0., 1., 0.), "Z"))
    child = (((0., 0., 1.), "Y"), ((1., 1., 0.), "X"),
             ((1., 0., 1.), "Z"))
    angle = .731
    cosine, sine = math.cos(angle), math.sin(angle)
    rotation = ((cosine, -sine, 0.), (sine, cosine, 0.), (0., 0., 1.))
    shift = (3.2, -1.7, 4.1)

    def moved(block):
        return tuple((tuple(sum(rotation[i][j] * point[j]
                                for j in range(3)) + shift[i]
                            for i in range(3)), color)
                     for point, color in reversed(block))
    left = macro_features(parent, child, 1.)
    right = macro_features(moved(parent), moved(child), 1.)
    assert max(abs(a - b) for a, b in zip(left, right)) < 1e-10


if __name__ == "__main__":
    test_parent_child_macro_dataset()
    test_macro_feature_rigid_and_permutation_invariance()
    print("parent-child macro dataset tests passed")
