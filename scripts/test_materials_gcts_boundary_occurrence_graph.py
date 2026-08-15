#!/usr/bin/env python3
"""Focused opt-in boundary-edge reducer/miner safety checks."""

from types import SimpleNamespace

from materials_gcts_macro_promotion import (
    MacroBoundaryPort, MacroBoundaryRelation)
from materials_gcts_oriented_overlap_ports import IDENTITY
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_sparse_occurrence_graph import reduce_occurrence_graph
from test_materials_gcts_port_graph_macros import _synthetic_program


def _with_boundary_witnesses():
    source = _synthetic_program()
    admitted_key = (303,)
    unadmitted_key = (404,)
    port = MacroBoundaryPort(
        0, 0, IDENTITY, (8., 10., 0.), admitted_key, 2, 2)
    relations = (
        MacroBoundaryRelation(2, 3, 0, 0, admitted_key, 1),
        # This relation must not enter the graph: no admitted port owns it.
        MacroBoundaryRelation(1, 4, 0, 0, unadmitted_key, 1))
    return SimpleNamespace(**vars(source), boundary_ports=(port,),
                           boundary_relation_classes=relations)


def test_boundary_relations_are_opt_in_witnessed_and_not_merged():
    program = _with_boundary_witnesses()
    baseline = reduce_occurrence_graph(program)
    explicit_baseline = reduce_occurrence_graph(
        program, include_boundary_relations=False)
    augmented = reduce_occurrence_graph(
        program, include_boundary_relations=True)
    assert baseline == explicit_baseline
    assert augmented.source_edges == baseline.source_edges + 1
    assert augmented.source_components == 1
    assert baseline.source_components == 2
    assert any(edge.connection_kind == "boundary"
               for edge in augmented.retained_edges)
    boundary_edges = tuple(edge for edge in augmented.retained_edges
                           if edge.connection_kind == "boundary")
    assert len(boundary_edges) == 1
    assert boundary_edges[0].canonical_port_label == (0, 0, (303,))
    assert boundary_edges[0].overlap_atoms == 0


def test_boundary_miner_keeps_overlap_only_ablation_stable():
    program = _with_boundary_witnesses()
    default = mine_port_graph_macros(
        program, maximum_nodes=3, geometry_tolerance=1e-6)
    explicit = mine_port_graph_macros(
        program, maximum_nodes=3, geometry_tolerance=1e-6,
        include_boundary_relations=False)
    augmented = mine_port_graph_macros(
        program, maximum_nodes=3, geometry_tolerance=1e-6,
        include_boundary_relations=True)
    assert default == explicit
    assert augmented.source_graph_edges == default.source_graph_edges + 1
    assert augmented.source_graph_vertices == default.source_graph_vertices


if __name__ == "__main__":
    test_boundary_relations_are_opt_in_witnessed_and_not_merged()
    test_boundary_miner_keeps_overlap_only_ablation_stable()
    print("witnessed boundary occurrence graph: all assertions passed")
