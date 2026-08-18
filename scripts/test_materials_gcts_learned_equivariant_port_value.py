#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_irregular_supports import _species_key
from materials_gcts_learned_equivariant_port_value import (
    LearnedEquivariantPortExample, LearnedEquivariantPortSpec,
    equivariant_port_interaction_embedding,
    fit_learned_equivariant_port_value,
    score_learned_equivariant_port_value,
    shuffle_equivariant_port_labels_within_groups)
from materials_gcts_partial_irregular_port_graph import (
    PartialIncidenceEdge, PartialIrregularPortGraph, PartialPortNode)


def _graph(chirality):
    nodes = tuple(sorted((
        PartialPortNode(1, _species_key("A"), 4, 5, 4),
        PartialPortNode(2, _species_key("B"), 5, 6, 4),
        PartialPortNode(3, _species_key("C"), 5, 7, 3))))
    edges = (
        PartialIncidenceEdge(
            0, 1, ((_species_key("X"), 2),), 4,
            ((_species_key("X"), (2, 3)),), chirality),
        PartialIncidenceEdge(
            1, 2, ((_species_key("Y"), 1),), 8,
            ((_species_key("Y"), (3, 5)),), 0))
    return PartialIrregularPortGraph(
        nodes, (), 0, ("p" if chirality > 0 else "n") * 64,
        incidence_edges=edges)


def test_equivariant_interactions_fit_recurrent_port_conjunctions():
    positive, negative = _graph(1), _graph(-1)
    rows = tuple(LearnedEquivariantPortExample(group, graph, label)
                 for group in range(4)
                 for graph, label in ((positive, True), (negative, False)))
    spec = LearnedEquivariantPortSpec(
        interaction_order=3, ridge=.1, steps=180)
    first = fit_learned_equivariant_port_value(rows, spec)
    second = fit_learned_equivariant_port_value(tuple(reversed(rows)), spec)
    assert first.model_digest == second.model_digest
    assert score_learned_equivariant_port_value(first, positive) > \
        score_learned_equivariant_port_value(first, negative)
    assert any(key[0:2] == ("message", "mean") and
               "source-port-neighbor" in key
               for key in first.feature_keys)
    assert not first.target_used
    ranked = fit_learned_equivariant_port_value(
        rows, replace(spec, objective="pairwise"))
    assert score_learned_equivariant_port_value(ranked, positive) > \
        score_learned_equivariant_port_value(ranked, negative)


def test_equivariant_embedding_is_node_permutation_invariant():
    graph = _graph(1)
    size = len(graph.nodes)
    permuted = replace(
        graph, nodes=tuple(reversed(graph.nodes)),
        incidence_edges=tuple(replace(
            edge,
            left_index=min(size - 1 - edge.left_index,
                           size - 1 - edge.right_index),
            right_index=max(size - 1 - edge.left_index,
                            size - 1 - edge.right_index))
            for edge in reversed(graph.incidence_edges)))
    spec = LearnedEquivariantPortSpec(interaction_order=3)
    first = dict(equivariant_port_interaction_embedding(graph, spec))
    second = dict(equivariant_port_interaction_embedding(permuted, spec))
    assert first.keys() == second.keys()
    assert max(abs(first[key] - second[key]) for key in first) < 1e-12


def test_shuffle_preserves_groups_and_target_taint_fails():
    rows = tuple(LearnedEquivariantPortExample(
        group, _graph(1 if label else -1), label)
        for group in range(3) for label in (True, False, True))
    shuffled = shuffle_equivariant_port_labels_within_groups(rows, seed=19)
    for group in range(3):
        assert sum(row.successful for row in rows if row.group == group) == \
            sum(row.successful for row in shuffled if row.group == group)
    try:
        equivariant_port_interaction_embedding(
            replace(_graph(1), target_used=True))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted graph entered learned messages")


if __name__ == "__main__":
    test_equivariant_interactions_fit_recurrent_port_conjunctions()
    test_equivariant_embedding_is_node_permutation_invariant()
    test_shuffle_preserves_groups_and_target_taint_fails()
    print("learned equivariant port-value tests passed")
