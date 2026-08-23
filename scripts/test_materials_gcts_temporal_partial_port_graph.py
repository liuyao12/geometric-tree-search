#!/usr/bin/env python3
"""Metamorphic tests for temporal partial-support incidence."""

from dataclasses import replace

from materials_gcts_partial_irregular_section import (
    PartialIrregularSection, PartialSupportMatch)
from materials_gcts_temporal_partial_port_graph import (
    TemporalPortGraphExample, TemporalPortGraphValueSpec,
    fit_temporal_port_graph_value, score_temporal_port_graph_value,
    temporal_partial_port_graph, temporal_partial_port_graph_embedding,
    temporal_partial_port_prefix)


def section(rows):
    matches = tuple(PartialSupportMatch(
        index, type_id, len(support), 4, len(support) / 4, 3, 10, support)
        for index, (type_id, support) in enumerate(rows))
    return PartialIrregularSection(
        matches, .5, .625, 2, (0,), 0, 0., 0, 0, True)


def test_temporal_graph_is_rigid_and_permutation_invariant():
    seed = ((0., 0., 0.), (0., 1., 0.))
    colors = ("X", "Y")
    blocks = (
        (((1., 0., 0.), "X"), ((1., 1., 0.), "Y")),
        (((2., 0., 1.), "X"), ((2., 1., 1.), "Y")))
    sections = (
        section(((7, (0, 2)), (8, (1, 3)))),
        section(((9, (0, 2, 4)), (10, (1, 3, 5)))))
    graph = temporal_partial_port_graph(
        sections, blocks, seed, colors, distance_scale=1.)
    permuted_blocks = (
        (blocks[0][1], blocks[0][0]), (blocks[1][1], blocks[1][0]))
    permuted_sections = (
        section(((8, (1, 2)), (7, (0, 3)))),
        section(((10, (1, 2, 4)), (9, (0, 3, 5)))))
    permuted = temporal_partial_port_graph(
        permuted_sections, permuted_blocks, seed, colors, distance_scale=1.)
    transform = lambda point: (-point[1] + 11., point[0] - 7.,
                               point[2] + 3.)
    moved = temporal_partial_port_graph(
        sections,
        tuple(tuple((transform(point), color) for point, color in block)
              for block in blocks),
        tuple(transform(point) for point in seed), colors, distance_scale=1.)
    assert graph.canonical_digest == permuted.canonical_digest == \
        moved.canonical_digest
    assert temporal_partial_port_graph_embedding(graph) == \
        temporal_partial_port_graph_embedding(permuted)
    assert graph.dependency_edges == 2
    prefix = temporal_partial_port_prefix(graph, 1)
    assert len(prefix.nodes) == 2 and len(prefix.edges) == 1
    assert prefix.stages == 1 and prefix.dependency_edges == 0
    assert not graph.raw_atom_ids_retained and not graph.target_used
    bad = replace(graph, edges=tuple(
        replace(edge, separation_bin=edge.separation_bin + 10)
        for edge in graph.edges), canonical_digest="bad")
    examples = tuple(TemporalPortGraphExample(
        group, 0, candidate, successful)
        for group in ("a", "b", "c")
        for candidate, successful in ((graph, True), (bad, False)))
    model = fit_temporal_port_graph_value(
        examples, TemporalPortGraphValueSpec(
            ridge=1., steps=60, parent_conditional=True))
    assert score_temporal_port_graph_value(model, graph) > \
        score_temporal_port_graph_value(model, bad)
    try:
        temporal_partial_port_graph_embedding(replace(graph, target_used=True))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted temporal graph was accepted")


if __name__ == "__main__":
    test_temporal_graph_is_rigid_and_permutation_invariant()
    print("temporal partial port graph test passed")
