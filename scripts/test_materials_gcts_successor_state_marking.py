#!/usr/bin/env python3
"""Focused checks for causal successor-frontier descriptors."""

from collections import Counter

from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionState)
from materials_gcts_successor_state_marking import (
    path_state_descriptor, rollout_state_descriptor,
    successor_outgoing_points, successor_state_descriptor)
from materials_gcts_port_incidence_search import (
    port_incidence_patterns, port_incidence_state)


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
    state = port_incidence_state(first, first.votes)
    patterns = port_incidence_patterns(first, first.votes)
    path = path_state_descriptor(
        descriptor, rotated_descriptor, root_color="A", child_color="B",
        normalized_distance_bin=4, incoming_state=state,
        incoming_patterns=patterns)
    assert ("path-colors", "A", "B") in path.tokens
    assert any(token[0] == "path-incoming-role" for token in path.tokens)
    # A newly placed site can be the ordered source rather than the affine
    # parent.  It still causally exposes the action and must enter the
    # successor frontier without corrupting the geometric parent role.
    source_enabled = MarkedProposalResult(
        Counter({(2., 0., 0.): 1}), 1, None,
        {(2., 0., 0.): Counter({"B": 1})},
        {(2., 0., 0.): Counter({"B": 1})},
        {(2., 0., 0.): Counter({})},
        {(2., 0., 0.): Counter({0: 1})},
        {(2., 0., 0.): Counter({0: 1, 1: 1})})
    assert successor_outgoing_points(
        source_enabled, new_parent_index=1,
        occupied_positions=((0., 0., 0.), (1., 0., 0.)),
        minimum_distance=.5) == ((2., 0., 0.),)
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
