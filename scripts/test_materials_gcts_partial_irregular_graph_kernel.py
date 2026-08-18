#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_irregular_supports import _species_key
from materials_gcts_partial_irregular_graph_kernel import (
    PartialGraphKernelExample, PartialGraphKernelSpec,
    fit_partial_graph_kernel, partial_graph_distance,
    score_partial_graph_kernel)
from materials_gcts_partial_irregular_port_graph import (
    PartialIrregularPortGraph, PartialPortEdge, PartialPortNode)


def _graph(type_id, separation, chirality, species="A"):
    first = PartialPortNode(type_id, _species_key(species), 4, 5, 4)
    second = PartialPortNode(type_id + 1, _species_key("B"), 5, 6, 4)
    nodes = tuple(sorted((first, second)))
    edge = PartialPortEdge(
        nodes, ((_species_key("X"), 2),), separation,
        ((_species_key("X"), (2, 3)),), chirality)
    return PartialIrregularPortGraph(
        nodes, (edge,), 0, f"{type_id:064x}")


def test_continuous_kernel_orders_nearby_port_graphs_and_scores_labels():
    reference = _graph(1, 4, 1)
    nearby = _graph(1, 5, 1)
    wrong_chemistry = _graph(8, 9, -1, "Q")
    spec = PartialGraphKernelSpec(3, .25, 1., 1., .5)
    assert partial_graph_distance(reference, nearby, spec) < \
        partial_graph_distance(reference, wrong_chemistry, spec)
    rows = tuple(PartialGraphKernelExample(group, graph, label)
                 for group in range(3)
                 for graph, label in ((reference, True),
                                      (wrong_chemistry, False)))
    model = fit_partial_graph_kernel(rows, spec)
    assert score_partial_graph_kernel(model, nearby) > \
        score_partial_graph_kernel(model, wrong_chemistry)
    assert not model.target_used


def test_kernel_rejects_target_taint():
    graph = _graph(1, 4, 0)
    tainted = replace(graph, target_used=True)
    try:
        partial_graph_distance(graph, tainted)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph entered the kernel")


if __name__ == "__main__":
    test_continuous_kernel_orders_nearby_port_graphs_and_scores_labels()
    test_kernel_rejects_target_taint()
    print("partial irregular graph-kernel tests passed")
