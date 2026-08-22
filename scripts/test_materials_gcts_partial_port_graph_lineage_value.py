#!/usr/bin/env python3
"""Focused invariants for bounded finite port-graph lineage value."""

from dataclasses import replace

from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortNode)
from materials_gcts_partial_port_graph_lineage_value import (
    PartialPortGraphLineageExample, PartialPortGraphLineageSpec,
    fit_partial_port_graph_lineage_value,
    partial_port_graph_lineage_embedding,
    score_partial_port_graph_lineage_value)


def graph(kind, separation, digest):
    first = PartialPortNode(kind, ("X",), 2, 3, 4)
    second = PartialPortNode(kind + 1, ("Y",), 2, 3, 4)
    edge = PartialIncidenceEdge(
        0, 1, ((("X",), 1),), separation, ((("X",), (1, 2)),), 1, True)
    return PartialIrregularPortGraph(
        (first, second), (), 0, digest, incidence_edges=(edge,))


def test_lineage_value():
    good = (graph(1, 3, "g0"), graph(2, 4, "g1"), graph(3, 5, "g2"))
    bad = (graph(1, 9, "b0"), graph(2, 10, "b1"), graph(3, 11, "b2"))
    rows = tuple(
        PartialPortGraphLineageExample(group, parent, graphs, successful)
        for group in ("a", "b", "c")
        for parent, graphs, successful in ((0, good, True), (0, bad, False)))
    spec = PartialPortGraphLineageSpec(
        minimum_feature_groups=2, ridge=1., steps=80,
        parent_conditional=True)
    model = fit_partial_port_graph_lineage_value(rows, spec)
    assert score_partial_port_graph_lineage_value(model, good) > \
        score_partial_port_graph_lineage_value(model, bad)
    assert not model.target_used and model.feature_keys
    assert partial_port_graph_lineage_embedding(good, spec) == \
        partial_port_graph_lineage_embedding(good, spec)
    tainted = replace(good[0], target_used=True)
    try:
        partial_port_graph_lineage_embedding((tainted,) + good[1:], spec)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph entered lineage value")


if __name__ == "__main__":
    test_lineage_value()
    print("partial port-graph lineage value test passed")
