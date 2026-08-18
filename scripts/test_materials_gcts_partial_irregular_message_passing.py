#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_irregular_supports import _species_key
from materials_gcts_partial_irregular_message_passing import (
    PartialMessagePassingExample, PartialMessagePassingSpec,
    fit_partial_message_passing_value, message_embedding_distance,
    partial_message_passing_embedding, score_partial_message_passing_value)
from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortEdge,
    PartialPortNode)


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
    incidence = tuple(PartialIncidenceEdge(
        left, right, edge.shared_species, edge.separation_bin,
        edge.shared_distance_profiles, edge.chirality)
        for (left, right), edge in zip(
            ((0, 1), (0 if branch else 1, 2)), edges))
    return PartialIrregularPortGraph(
        nodes, tuple(sorted(edges)), 0,
        ("b" if branch else "p") * 64, incidence_edges=incidence)


def _duplicate_node_graph(shared_center):
    repeated = PartialPortNode(1, _species_key("A"), 4, 5, 4)
    nodes = tuple(sorted((
        repeated, repeated,
        PartialPortNode(2, _species_key("B"), 5, 6, 4),
        PartialPortNode(3, _species_key("C"), 5, 7, 3))))
    edge_ab = _edge(nodes[0], nodes[2], separation=4)
    edge_ac = _edge(nodes[1], nodes[3], separation=8)
    second_left = 0 if shared_center else 1
    incidence = (
        PartialIncidenceEdge(0, 2, edge_ab.shared_species,
                             edge_ab.separation_bin,
                             edge_ab.shared_distance_profiles, 0),
        PartialIncidenceEdge(second_left, 3, edge_ac.shared_species,
                             edge_ac.separation_bin,
                             edge_ac.shared_distance_profiles, 0))
    return PartialIrregularPortGraph(
        nodes, tuple(sorted((edge_ab, edge_ac))), 0,
        ("s" if shared_center else "d") * 64,
        incidence_edges=incidence)


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
    size = len(graph.nodes)
    permuted = replace(graph, nodes=tuple(reversed(graph.nodes)),
                       edges=tuple(reversed(graph.edges)),
                       incidence_edges=tuple(replace(
                           edge,
                           left_index=min(size - 1 - edge.left_index,
                                          size - 1 - edge.right_index),
                           right_index=max(size - 1 - edge.left_index,
                                           size - 1 - edge.right_index))
                           for edge in reversed(graph.incidence_edges)))
    mirrored = replace(graph, edges=tuple(
        replace(edge, chirality=-edge.chirality) for edge in graph.edges),
        incidence_edges=tuple(replace(edge, chirality=-edge.chirality)
                              for edge in graph.incidence_edges))
    spec = PartialMessagePassingSpec(depth=2)
    expected = partial_message_passing_embedding(graph, spec)
    assert partial_message_passing_embedding(permuted, spec) == expected
    assert partial_message_passing_embedding(mirrored, spec) != expected


def test_message_passing_preserves_incidence_between_duplicate_node_types():
    shared = _duplicate_node_graph(True)
    distributed = _duplicate_node_graph(False)
    depth0 = PartialMessagePassingSpec(depth=0)
    depth1 = PartialMessagePassingSpec(depth=1)
    assert message_embedding_distance(
        partial_message_passing_embedding(shared, depth0),
        partial_message_passing_embedding(distributed, depth0)) == 0
    assert message_embedding_distance(
        partial_message_passing_embedding(shared, depth1),
        partial_message_passing_embedding(distributed, depth1)) > 0


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
    test_message_passing_preserves_incidence_between_duplicate_node_types()
    test_message_passing_rejects_target_taint()
    print("partial irregular message-passing tests passed")
