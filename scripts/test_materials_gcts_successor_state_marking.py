#!/usr/bin/env python3
"""Focused checks for causal successor-frontier descriptors."""

from collections import Counter

from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionState)
from materials_gcts_successor_state_marking import (
    rollout_state_descriptor, successor_state_descriptor)


def fixture(transform=lambda point: point):
    parent = transform((0., 0., 0.))
    left = transform((2., 0., 0.))
    right = transform((0., 2., 0.))
    state = RecursiveConnectionState(
        LocalClusterType("A", (1,)), LocalClusterType("B", (2,)), 2)
    proposals = MarkedProposalResult(
        Counter({left: 4, right: 3}), 0, None,
        {left: Counter({"B": 4}), right: Counter({"A": 3})},
        {left: Counter({"B": 4}), right: Counter({"A": 3})},
        {left: Counter({state: 4}), right: Counter({state: 3})},
        {left: Counter({0: 4}), right: Counter({0: 3})})
    return proposals, parent


def main():
    first, parent = fixture()
    descriptor = successor_state_descriptor(
        first, new_parent_index=0, new_parent_position=parent,
        occupied_positions=(parent,), minimum_distance=1., distance_scale=1.)
    rotated, rotated_parent = fixture(
        lambda point: (7. - point[1], -3. + point[0], 11. + point[2]))
    rotated_descriptor = successor_state_descriptor(
        rotated, new_parent_index=0, new_parent_position=rotated_parent,
        occupied_positions=(rotated_parent,), minimum_distance=1.,
        distance_scale=1.)
    assert descriptor == rotated_descriptor
    assert ("successor-outgoing-count", 2) in descriptor.tokens
    assert any(token[0] == "successor-pattern" for token in descriptor.tokens)
    rollout = rollout_state_descriptor(
        descriptor, (rotated_descriptor, descriptor))
    reversed_rollout = rollout_state_descriptor(
        descriptor, (descriptor, rotated_descriptor))
    assert rollout == reversed_rollout
    assert ("rollout-branch-count", 2) in rollout.tokens
    try:
        successor_state_descriptor(
            first, new_parent_index=1, new_parent_position=parent,
            occupied_positions=(parent,), minimum_distance=1., distance_scale=1.)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown parent index must fail closed")
    print("successor-state marking tests passed")


if __name__ == "__main__":
    main()
