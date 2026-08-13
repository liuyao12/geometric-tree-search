#!/usr/bin/env python3

from materials_gcts_cross_family_transfer_audit import _learn_anchor
from materials_gcts_fibonacci_3d import PHI, make_input
from materials_gcts_geometry_vm import compile_anchor
from materials_gcts_geometry_vm_benchmark import _crystal, _fibonacci, _iqc
from materials_gcts_port_cover_graph import compile_instruction


def test_one_recursive_cover_graph_executes_all_systems_exactly() -> None:
    # These benchmark adapters execute the normalized graph, not VM dispatch.
    for case in (_crystal(), _iqc(), _fibonacci()):
        assert case.exact_species_and_positions


def test_graph_node_has_uniform_recursive_contract() -> None:
    seed = make_input(9)
    edges = (1.1, 1.7, 2.4, 3.0)
    _, anchor = _learn_anchor(seed, PHI, edges)
    graph = compile_instruction(compile_anchor(seed, PHI, edges, anchor))
    assert graph.root_nodes == ("root",)
    assert len(graph.nodes) == 1
    node = graph.nodes[0]
    assert node.child_nodes == ("root",)
    assert node.domain.arity == len(node.output.coefficients)
    assert node.domain.relation
    assert node.connection.predicate
    assert node.color.predicate


if __name__ == "__main__":
    test_one_recursive_cover_graph_executes_all_systems_exactly()
    test_graph_node_has_uniform_recursive_contract()
    print("recursive port/cover graph: benchmark passed")
