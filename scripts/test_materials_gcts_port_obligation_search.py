#!/usr/bin/env python3

from collections import Counter

from materials_gcts_frontier_band_marking import frontier_score_bands
from materials_gcts_port_obligation_search import (
    LOOKAHEAD_BAND_FEATURE_NAMES, describe_port_obligations,
    lookahead_band_features)
from materials_gcts_recursive_connections import (
    LocalClusterType, MarkedProposalResult, RecursiveConnectionMarking,
    RecursiveConnectionState, StateEvidence)


TYPE_A = LocalClusterType("A", (2, 4))
TYPE_B = LocalClusterType("B", (3, 5))
STATE = RecursiveConnectionState(TYPE_A, TYPE_B, 2)


def _proposal(points):
    return MarkedProposalResult(
        Counter({point: index + 1 for index, point in enumerate(points)}),
        0, None,
        {point: Counter({"A": index + 1})
         for index, point in enumerate(points)},
        {point: Counter({"B": 1}) for point in points},
        {point: Counter({STATE: index + 1})
         for index, point in enumerate(points)},
        {point: Counter({index: index + 1})
         for index, point in enumerate(points)})


def test_carried_obligation_features_are_finite_and_order_invariant():
    before = _proposal(((1., 0., 0.), (0., 1., 0.)))
    after = _proposal(((0., 0., 1.), (1., 1., 0.), (1., 0., 1.)))
    marking = RecursiveConnectionMarking(
        1.6, .5, (TYPE_A, TYPE_B), {STATE: StateEvidence(8, 10)},
        frozenset((STATE,)), 2, .7, {STATE: Counter({"B": 8})})
    scores = {(1., 0., 0.): .8, (0., 1., 0.): .6}
    band = frontier_score_bands(before, scores)[0]
    features = lookahead_band_features(
        band.features, before, after, marking)
    reordered = _proposal(tuple(reversed(tuple(after.votes))))
    assert describe_port_obligations(after, marking) == \
        describe_port_obligations(reordered, marking)
    assert len(features) == len(LOOKAHEAD_BAND_FEATURE_NAMES)
    assert features != band.features


if __name__ == "__main__":
    test_carried_obligation_features_are_finite_and_order_invariant()
    print("port obligation search tests: passed")
