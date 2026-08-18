#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_irregular_supports import _species_key
from materials_gcts_partial_irregular_port_graph import (
    PartialIrregularPortGraph, PartialPortEdge, PartialPortNode)
from materials_gcts_partial_irregular_port_value import (
    PartialPortGraphExample, PartialPortGraphValueSpec,
    fit_partial_port_graph_value, score_partial_port_graph)


def _graph(left, right, separation, chirality=0):
    first = PartialPortNode(left, _species_key("A"), 4, 5, 3)
    second = PartialPortNode(right, _species_key("B"), 4, 6, 3)
    nodes = tuple(sorted((first, second)))
    edge = PartialPortEdge(
        nodes, ((_species_key("X"), 2),), separation,
        ((_species_key("X"), (2, 3)),
         (_species_key("X"), (3, 4))), chirality)
    code = (nodes, (edge,))
    return PartialIrregularPortGraph(nodes, (edge,), 0, repr(code))


def test_finite_port_graph_value_uses_group_supported_backoff():
    good = _graph(1, 2, 4, 1)
    bad = _graph(3, 4, 8, -1)
    rows = tuple(PartialPortGraphExample(group, graph, label)
                 for group in range(3)
                 for graph, label in ((good, True), (bad, False)))
    model = fit_partial_port_graph_value(
        rows, PartialPortGraphValueSpec(2, 2, .5))
    assert score_partial_port_graph(model, good).probability > \
        score_partial_port_graph(model, bad).probability
    assert score_partial_port_graph(model, good).backoff_level == "exact"

    # Unseen support IDs retain the same oriented colored port geometry and
    # therefore use the final train-supported port-semantic backoff.
    unseen = _graph(10, 11, 4, 1)
    score = score_partial_port_graph(model, unseen)
    assert score.backoff_level == "ports"
    assert score.train_supported
    assert not model.target_used


def test_target_taint_fails_closed():
    good = _graph(1, 2, 4)
    tainted = replace(good, target_used=True)
    rows = (PartialPortGraphExample(0, good, True),
            PartialPortGraphExample(1, good, True))
    model = fit_partial_port_graph_value(rows)
    try:
        score_partial_port_graph(model, tainted)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph was ranked")


if __name__ == "__main__":
    test_finite_port_graph_value_uses_group_supported_backoff()
    test_target_taint_fails_closed()
    print("partial irregular-port value tests passed")
