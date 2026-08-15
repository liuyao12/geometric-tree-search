#!/usr/bin/env python3

from materials_gcts_port_graph_macro_benchmark import evaluate


def main() -> None:
    cases = evaluate()
    assert tuple(case.system for case in cases) == (
        "NaCl-rocksalt", "Icosahedral-6D-model-set",
        "Cd5.7Yb-offcenter-seed")
    for case in cases:
        assert case.sparse_nodes < case.source_nodes
        assert case.sparse_undirected_edges < case.source_edges
        assert case.node_reduction > .90
        assert case.edge_reduction > .99
        assert case.positive_mdl_macro_types > 0
        assert case.maximum_macro_nodes == 2
        assert case.maximum_macro_atoms > 0
        assert case.maximum_mdl_saving > 0
        assert case.minimum_independent_occurrences >= 2
        assert case.maximum_cycle_residual <= 1e-6
        assert case.exact_graph_and_se3_verified
        assert case.family_label_cell_potential_target_unused
    # The difficult real-model case remains sparse after strict independent
    # recurrence and MDL gates; this is evidence, not a relaxed expectation.
    assert cases[2].positive_mdl_macro_types <= 2
    print("cross-family first-level port-graph macros: passed", cases)


if __name__ == "__main__":
    main()
