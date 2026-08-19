#!/usr/bin/env python3
"""Fast positive and target-taint controls for graph value fitting."""

from dataclasses import replace

from materials_gcts_child_frontier_graph import (
    ChildFrontierAction, ChildFrontierNode, child_frontier_graph)
from materials_gcts_child_frontier_graph_value import (
    ChildFrontierGraphExample, ChildFrontierGraphUtilityExample,
    ChildFrontierGraphValueSpec, fit_child_frontier_graph_utility_value,
    fit_child_frontier_graph_value, score_child_frontier_graph_utility_value,
    score_child_frontier_graph_value)


def _graph(outgoing, group):
    node = ChildFrontierNode(
        "X", (group,), 1, 1, (("incoming",),), 1,
        (("outgoing", outgoing),), outgoing, ("Y",) if outgoing else (),
        not outgoing)
    return child_frontier_graph((ChildFrontierAction(
        node, (0., 0., 0.), (((2., 0., 0.), "Y"),) if outgoing else ()),),
        minimum_distance=1., distance_scale=1.)


def test_graph_value_prefers_recurrent_outgoing_obligations():
    rows = tuple(ChildFrontierGraphExample(group, _graph(label, label), label)
                 for group in range(3) for label in (False, True))
    model = fit_child_frontier_graph_value(rows, ChildFrontierGraphValueSpec(
        interaction_order=2, minimum_feature_groups=2, steps=40))
    assert score_child_frontier_graph_value(model, _graph(True, True)) > \
        score_child_frontier_graph_value(model, _graph(False, False))
    tainted = replace(_graph(True, True), target_used=True)
    try:
        score_child_frontier_graph_value(model, tainted)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph was accepted")


def test_ordinal_utility_prefers_more_productive_frontiers():
    rows = tuple(ChildFrontierGraphUtilityExample(
        group, _graph(level > 0, level > 1), level)
        for group in range(3) for level in range(3))
    model = fit_child_frontier_graph_utility_value(rows,
        ChildFrontierGraphValueSpec(
            interaction_order=2, minimum_feature_groups=2, steps=40))
    scores = tuple(score_child_frontier_graph_utility_value(
        model, _graph(level > 0, level > 1)) for level in range(3))
    assert scores[2] > scores[1] > scores[0]
    try:
        score_child_frontier_graph_utility_value(
            model, replace(_graph(True, True), target_used=True))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted utility graph was accepted")


if __name__ == "__main__":
    test_graph_value_prefers_recurrent_outgoing_obligations()
    test_ordinal_utility_prefers_more_productive_frontiers()
    print("child-frontier graph value tests passed")
