#!/usr/bin/env python3

from materials_gcts_sparse_occurrence_graph_benchmark import evaluate


def main() -> None:
    cases = evaluate()
    assert len(cases) == 3
    for case in cases:
        assert case.complete_repeated_support_cover
        assert case.retained_nodes <= case.source_nodes
        assert case.retained_edges <= case.source_edges
        assert case.spanning_edges == case.retained_nodes - case.retained_components
        assert case.connected_when_source_connected
        assert case.generic_inputs_only
        assert 0 <= case.node_reduction <= 1
        assert 0 <= case.edge_reduction <= 1
    print("sparse occurrence graph reduction: passed", cases)


if __name__ == "__main__":
    main()
