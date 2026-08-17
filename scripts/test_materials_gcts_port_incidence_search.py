#!/usr/bin/env python3
"""Adversarial tests for explicit carried-port GCTS search."""

from collections import Counter

from materials_gcts_port_incidence_search import (
    PortIncidenceAction, PortIncidenceState, fit_port_incidence_policy,
    port_incidence_patterns, port_incidence_state, search_port_incidence_paths,
    semantic_port_role)
from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionState)


def _state(parent, source, separation):
    return RecursiveConnectionState(
        LocalClusterType(parent, (2, 5)),
        LocalClusterType(source, (1, 4)), separation)


def _proposal(rows):
    votes = Counter()
    state_votes = {}
    for point, state, count in rows:
        votes[point] += count
        state_votes.setdefault(point, Counter())[state] += count
    return MarkedProposalResult(votes, 0, None, {}, {}, state_votes, {})


def _incidence(*rows):
    proposals = _proposal(tuple(
        ((float(index), 0., 0.), state, count)
        for index, (state, count) in enumerate(rows)))
    return port_incidence_state(proposals, maximum_roles=4)


def test_semantic_state_is_order_and_identity_free():
    left = _state("Na", "Cl", 3)
    right = _state("Cl", "Na", 4)
    first = _proposal((((1., 0., 0.), left, 2),
                       ((2., 0., 0.), right, 1)))
    second = _proposal((((2., 0., 0.), right, 1),
                        ((1., 0., 0.), left, 2)))
    assert port_incidence_state(first) == port_incidence_state(second)
    assert port_incidence_patterns(
        first, first.votes) == port_incidence_patterns(second, second.votes)
    assert semantic_port_role(left).parent_color == "Na"


def test_search_backtracks_from_stranded_high_score_action():
    incoming = _state("A", "B", 2)
    good = _state("B", "C", 3)
    bad = _state("B", "X", 8)
    terminal = PortIncidenceState((), 0, 0)
    good_required = _incidence((good, 2))
    bad_required = _incidence((bad, 2))
    root_bad = PortIncidenceAction(
        "root-bad", terminal, bad_required, 10., 2)
    root_good = PortIncidenceAction(
        "root-good", _incidence((incoming, 1)), good_required, 5., 2)
    child_good = PortIncidenceAction(
        "child-good", good_required, terminal, 1., 1)
    examples = tuple(
        (PortIncidenceAction(index, terminal, good_required, 0., 1), True)
        for index in range(3)) + tuple(
        (PortIncidenceAction(f"n{index}", terminal, bad_required, 0., 1),
         False) for index in range(3))
    policy = fit_port_incidence_policy(
        examples, minimum_positive_support=2, minimum_purity=.8)
    children = {"root-bad": (), "root-good": (child_good,),
                "child-good": ()}
    trace = search_port_incidence_paths(
        (root_bad, root_good), lambda action: children[action.action_id],
        policy, maximum_depth=2)
    assert trace.selected_ids == ("root-good", "child-good")
    assert trace.satisfied_obligation_mass == 2
    assert trace.backtracks >= 1
    assert trace.target_used is False


def test_disconnected_child_cannot_fake_obligation_discharge():
    role = _incidence((_state("A", "B", 2), 2))
    other = _incidence((_state("X", "Y", 7), 2))
    empty = PortIncidenceState((), 0, 0)
    root = PortIncidenceAction("root", empty, role, 1., 1)
    child = PortIncidenceAction("child", other, empty, 1., 1)
    policy = fit_port_incidence_policy(
        tuple((PortIncidenceAction(index, empty, role, 0., 1), True)
              for index in range(2)), minimum_positive_support=2)
    trace = search_port_incidence_paths(
        (root,), lambda action: (child,) if action.action_id == "root" else (),
        policy, maximum_depth=2)
    assert trace.selected_ids == ()
    assert trace.backtracks >= 1


def main():
    test_semantic_state_is_order_and_identity_free()
    test_search_backtracks_from_stranded_high_score_action()
    test_disconnected_child_cannot_fake_obligation_discharge()
    print("port incidence search tests passed")


if __name__ == "__main__":
    main()
