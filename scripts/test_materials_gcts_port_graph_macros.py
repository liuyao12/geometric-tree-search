#!/usr/bin/env python3

from types import SimpleNamespace

from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, OrientedOverlapPort, PortAtlas,
    make_prototype)
from materials_gcts_port_graph_macros import mine_port_graph_macros


def _synthetic_program():
    prototype = make_prototype(0, (
        ("A", (0., 0., 0.)), ("A", (1., 0., 0.)),
        ("B", (0., 1., 0.)), ("C", (0., 0., 1.))))
    occurrences = tuple(ClusterOccurrence(
        index, 0, IDENTITY,
        ((index % 3) * 1., (index // 3) * 10., 0.))
        for index in range(6))
    step_key = (101,)
    double_key = (202,)
    step = OrientedOverlapPort(
        0, 0, IDENTITY, (1., 0., 0.), ((1, 0),), ("A",),
        step_key, 4)
    double = OrientedOverlapPort(
        0, 0, IDENTITY, (2., 0., 0.), (), (), double_key, 2)
    relations = []
    for offset in (0, 3):
        relations.extend((
            (offset, offset + 1, 0, 0, step_key),
            (offset + 1, offset + 2, 0, 0, step_key),
            (offset, offset + 2, 0, 0, double_key)))
    atlas = PortAtlas(
        (step, double), len(relations), 0, 0, 0, 0, tuple(relations))
    supports = (
        (0, (0, 1, 2, 3)), (1, (1, 4, 5, 6)),
        (2, (4, 7, 8, 9)),
        (3, (20, 21, 22, 23)), (4, (21, 24, 25, 26)),
        (5, (24, 27, 28, 29)))
    return SimpleNamespace(
        prototypes=(prototype,), occurrences=occurrences,
        occurrence_supports=supports, atlas=atlas,
        minimum_shared_atoms=1)


def test_synthetic_exact_cycle_consistent_macro_is_mined():
    result = mine_port_graph_macros(
        _synthetic_program(), maximum_nodes=3,
        geometry_tolerance=1e-6)
    paths = tuple(macro for macro in result.macro_types
                  if len(macro.node_types) == 3 and len(macro.edges) >= 2)
    assert paths
    macro = paths[0]
    assert len(macro.occurrences) == 2
    assert all(occurrence.maximum_cycle_residual < 1e-12
               for occurrence in macro.occurrences)
    assert macro.mdl_saving > 0
    assert macro.exact_graph_isomorphism_verified
    assert macro.se3_cycle_consistent
    assert macro.maximum_occurrence_atom_overlap_fraction == 0.0
    assert len(macro.atom_union) == 10
    assert len(macro.child_placements) == 3
    assert all(set(left.atom_indices).isdisjoint(right.atom_indices)
               for index, left in enumerate(macro.occurrences)
               for right in macro.occurrences[index + 1:])
    assert any(candidate.boundary_slots for candidate in result.macro_types)


def test_nacl_witness_graph_has_reusable_positive_mdl_macros():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    program = compile_irregular_port_program(nacl.species, nacl.positions)
    result = mine_port_graph_macros(program, maximum_nodes=2)
    assert result.source_graph_vertices == len(program.occurrences)
    assert result.graph_vertices < result.source_graph_vertices
    assert result.sparse_undirected_edges < result.source_graph_edges
    assert result.sparse_node_reduction > .9
    assert result.sparse_edge_reduction > .99
    assert result.graph_edges > 0
    assert result.macro_types
    assert result.maximum_macro_nodes == 2
    assert all(len(macro.occurrences) >= 2 and macro.mdl_saving > 0
               for macro in result.macro_types)
    assert all(macro.exact_graph_isomorphism_verified and
               macro.se3_cycle_consistent and
               macro.maximum_occurrence_atom_overlap_fraction <= .1
               for macro in result.macro_types)
    assert all(occurrence.maximum_cycle_residual <= 1e-6
               for macro in result.macro_types
               for occurrence in macro.occurrences)
    assert any(macro.boundary_slots for macro in result.macro_types)


if __name__ == "__main__":
    test_synthetic_exact_cycle_consistent_macro_is_mined()
    test_nacl_witness_graph_has_reusable_positive_mdl_macros()
    print("recurring exact port-graph macros: passed")
