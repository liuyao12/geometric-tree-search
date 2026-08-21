"""Regression for generic molecular/connection/void discovery on ice."""

from collections import Counter

from materials_gcts_ice_cover import IceConfiguration, ice_ih
from materials_gcts_generic_ice_benchmark import evaluate
from materials_gcts_molecular_gap_clusters import learn_molecular_gap_cover


def test_generic_learner_discovers_water_and_gap_classes_in_both_ices() -> None:
    result = evaluate()
    assert result.benchmark_passed
    assert result.molecule_signature_transfers_across_polytypes
    assert result.void_signature_transfers_across_polytypes
    assert result.shared_connection_isometry_classes == 6
    assert result.finite_point_set_without_lattice_passed
    for case in result.cases:
        assert case.learned_formula == (("H", 2), ("O", 1))
        assert case.molecular_isometry_classes == 1
        assert case.inferred_component_degree_histogram in (((4, 72),), ((4, 64),))
        assert case.inferred_void_size_histogram in (((6, 180),), ((6, 128),))
        assert case.void_boundary_isometry_classes == 1
        assert case.exact_cover
        assert case.tree_search_recall == 1
        assert case.tree_search_backtracks == 0
        assert sum(case.commuting_wave_sizes) == case.molecular_occurrences - 1
        assert not case.material_label_used
        assert not case.expected_formula_used
        assert not case.expected_ring_size_used
        assert not case.physical_potential_used
    for case in result.finite_point_set_cases:
        assert case.exact_cover
        assert case.molecular_isometry_classes == 1
        assert case.void_boundary_isometry_classes == 1
        assert case.inferred_void_size_histogram[0][0] == 6
        assert case.tree_search_recall == 1


def test_extended_covalent_network_fails_over_instead_of_becoming_a_molecule() -> None:
    species = ("C",) * 8
    positions = tuple((1.4 * index, 0.0, 0.0) for index in range(8))
    result = learn_molecular_gap_cover(species, positions)
    assert result.extended_network_rejected
    assert not result.molecules
    assert result.residual_atoms == tuple(range(8))


def _fingerprint(configuration: IceConfiguration) -> tuple:
    result = learn_molecular_gap_cover(
        configuration.species, configuration.positions, cell=configuration.cell)
    return (
        result.molecule_type_count, result.connection_type_count, result.void_type_count,
        Counter(occurrence.formula for occurrence in result.molecules),
        Counter(occurrence.signature for occurrence in result.molecules),
        Counter(occurrence.signature for occurrence in result.connections),
        Counter(occurrence.signature for occurrence in result.void_boundaries),
        result.component_graph_connected, result.covered_atoms,
    )


def test_generic_ice_cover_is_permutation_and_proper_motion_invariant() -> None:
    source = ice_ih()
    permutation = tuple(reversed(range(len(source.positions))))
    permuted = IceConfiguration(
        "unlabelled-permuted",
        tuple(source.positions[index] for index in permutation),
        tuple(source.species[index] for index in permutation),
        source.cell,
    )
    rotate = lambda point: (-point[1], point[0], point[2])
    moved = IceConfiguration(
        "unlabelled-moved",
        tuple(rotate(point) for point in source.positions),
        source.species,
        tuple(rotate(vector) for vector in source.cell),  # type: ignore[arg-type]
    )
    assert _fingerprint(source) == _fingerprint(permuted)
    assert _fingerprint(source) == _fingerprint(moved)


if __name__ == "__main__":
    test_generic_learner_discovers_water_and_gap_classes_in_both_ices()
    test_extended_covalent_network_fails_over_instead_of_becoming_a_molecule()
    test_generic_ice_cover_is_permutation_and_proper_motion_invariant()
    print("generic ice molecule/connection/void benchmark: passed")
