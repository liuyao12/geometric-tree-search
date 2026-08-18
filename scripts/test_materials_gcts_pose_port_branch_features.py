#!/usr/bin/env python3

import math

from materials_gcts_pose_port_branch_features import (
    PosePortBranchAction, coupled_pose_port_branch_features,
    pose_port_branch_feature_names)


def _rotate(point):
    # Proper quarter turn around z, followed by a translation.
    x, y, z = point
    return (4. - y, -3. + x, 2. + z)


def test_branch_features_are_order_and_proper_frame_invariant():
    actions = (
        PosePortBranchAction("X", (0., 0., 0.), (1, -2)),
        PosePortBranchAction("Y", (1., 0., 0.), (3, 4)),
        PosePortBranchAction("X", (0., 2., 0.), (1, -2)),
    )
    expected = coupled_pose_port_branch_features(
        (3., .5), actions, color_keys=("X", "Y"),
        maximum_actions=3, channel_count=2)
    transformed = tuple(PosePortBranchAction(
        row.color, _rotate(row.position), row.channel_response)
        for row in reversed(actions))
    actual = coupled_pose_port_branch_features(
        (3., .5), transformed, color_keys=("X", "Y"),
        maximum_actions=3, channel_count=2)
    assert actual == expected
    assert all(math.isfinite(value) for value in actual)
    assert len(actual) == len(pose_port_branch_feature_names(
        ("depth", "score"), ("X", "Y"), maximum_actions=3,
        channel_count=2))


def test_color_and_port_response_remain_distinguishable():
    base = (1.,)
    action = PosePortBranchAction("X", (0., 0., 0.), (1, 2))
    neighbor = PosePortBranchAction("X", (1., 0., 0.), (3, 4))
    changed_color = PosePortBranchAction("Y", (1., 0., 0.), (3, 4))
    changed_port = PosePortBranchAction("X", (0., 0., 0.), (2, 1))
    kwargs = dict(color_keys=("X", "Y"), maximum_actions=2,
                  channel_count=2)
    first = coupled_pose_port_branch_features(
        base, (action, neighbor), **kwargs)
    assert first != coupled_pose_port_branch_features(
        base, (action, changed_color), **kwargs)
    assert first != coupled_pose_port_branch_features(
        base, (changed_port, neighbor), **kwargs)


if __name__ == "__main__":
    test_branch_features_are_order_and_proper_frame_invariant()
    test_color_and_port_response_remain_distinguishable()
    print("coupled pose-port branch features passed")
