#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_irregular_supports import _species_key
from materials_gcts_partial_irregular_message_passing import (
    PartialMessagePassingExample, PartialMessagePassingSpec,
    fit_partial_message_passing_value, message_embedding_distance,
    partial_message_passing_embedding, score_partial_message_passing_value)
from materials_gcts_partial_irregular_port_graph import (
    PartialIrregularPortGraph, PartialPortEdge, PartialPortNode)


def _edge(first, second, separation=4, chirality=0):
    ends = tuple(sorted((first, second)))
    return PartialPortEdge(
        ends, ((_species_key("X"), 2),), separation,
        ((_species_key("X"), (2, 3)),), chirality)


def _graph(branch=False, chirality=0):
    nodes = tuple(sorted((
        PartialPortNode(1, _species_key("A"), 4, 5, 4),
        PartialPortNode(2, _species_key("B"), 5, 6, 4),
        PartialPortNode(3, _species_key("C"), 5, 7, 3))))
    edges = (_edge(nodes[0], nodes[1], chirality=chirality),
             _edge(nodes[0 if branch else 1], nodes[2]))
    return PartialIrregularPortGraph(
        nodes, tuple(sorted(edges)), 0,
        ("b" if branch else "p") * 64)


def test_message_passing_distinguishes_incidence_and_scores_labels():
    path = _graph(False)
    branch = _graph(True)
    depth0 = PartialMessagePassingSpec(3, 0, .25, 1., .5)
    depth1 = replace(depth0, depth=1)
    assert message_embedding_distance(
        partial_message_passing_embedding(path, depth0),
        partial_message_passing_embedding(branch, depth0)) == 0
    assert message_embedding_distance(
        partial_message_passing_embedding(path, depth1),
        partial_message_passing_embedding(branch, depth1)) > 0
    rows = tuple(PartialMessagePassingExample(group, graph, label)
                 for group in range(3)
                 for graph, label in ((path, True), (branch, False)))
    model = fit_partial_message_passing_value(rows, depth1)
    assert score_partial_message_passing_value(model, path) > \
        score_partial_message_passing_value(model, branch)
    assert not model.target_used


def test_message_embedding_is_permutation_invariant_and_chirality_sensitive():
    graph = _graph(False, 1)
    permuted = replace(graph, nodes=tuple(reversed(graph.nodes)),
                       edges=tuple(reversed(graph.edges)))
    mirrored = replace(graph, edges=tuple(
        replace(edge, chirality=-edge.chirality) for edge in graph.edges))
    spec = PartialMessagePassingSpec(depth=2)
    expected = partial_message_passing_embedding(graph, spec)
    assert partial_message_passing_embedding(permuted, spec) == expected
    assert partial_message_passing_embedding(mirrored, spec) != expected


def test_message_passing_rejects_target_taint():
    try:
        partial_message_passing_embedding(replace(_graph(), target_used=True))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph entered message passing")


if __name__ == "__main__":
    test_message_passing_distinguishes_incidence_and_scores_labels()
    test_message_embedding_is_permutation_invariant_and_chirality_sensitive()
    test_message_passing_rejects_target_taint()
    print("partial irregular message-passing tests passed")
