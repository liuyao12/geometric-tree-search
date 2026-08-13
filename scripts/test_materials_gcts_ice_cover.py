#!/usr/bin/env python3

from materials_gcts_ice_cover import evaluate_all


def main() -> None:
    results = evaluate_all()
    assert {result.system for result in results} == {"ice-Ih", "ice-Ic"}
    for result in results:
        assert result.atoms >= 190
        assert result.water_molecules * 3 == result.atoms
        assert result.water_isometry_classes <= 2
        assert result.bridge_occurrences >= result.water_molecules
        assert result.ring_gap_occurrences > 0
        assert result.covered_atoms == result.atoms
        assert result.residual_atom_clusters == 0
        assert result.water_only_search_recall < .03
        assert result.connection_clusters_required
        assert result.reconstruction_recall == 1.0
        assert result.search_backtracks == 0
        assert not result.physical_potential_used
    print("ice molecular covering and connection search: passed")
    print(results)


if __name__ == "__main__":
    main()
