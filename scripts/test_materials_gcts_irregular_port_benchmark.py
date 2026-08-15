#!/usr/bin/env python3

from materials_gcts_irregular_port_benchmark import evaluate


def test_cross_family_irregular_supports_compile_to_finite_oriented_ports():
    result = evaluate()
    assert result.all_complete
    assert result.all_have_finite_ports
    assert result.all_poses_proper
    assert result.labels_cells_potentials_unused
    assert len(result.cases) == 3
    for case in result.cases:
        assert case.oriented_prototypes > 0
        assert case.fitted_occurrences > 0
        assert case.witnessed_overlap_relations >= case.finite_port_classes
        assert case.mean_atoms_shared_per_port >= 2


if __name__ == "__main__":
    test_cross_family_irregular_supports_compile_to_finite_oriented_ports()
    print("cross-family irregular oriented-port compiler: passed")
