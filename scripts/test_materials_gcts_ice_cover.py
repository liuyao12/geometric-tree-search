#!/usr/bin/env python3

import math

from materials_gcts_ice_cover import (
    _minimum_image,
    evaluate_all,
    ice_ic,
    ice_ih,
)


def _assert_bernal_fowler(configuration) -> None:
    oxygen_count = configuration.species.count("O")
    assert configuration.species[:oxygen_count] == ("O",) * oxygen_count
    assert configuration.species[oxygen_count:] == ("H",) * (2 * oxygen_count)
    oxygen = configuration.positions[:oxygen_count]
    directed_edges = []
    for donor, point in enumerate(oxygen):
        distances = sorted(
            (math.dist((0.0, 0.0, 0.0), _minimum_image(point, candidate, configuration.cell)), other)
            for other, candidate in enumerate(oxygen) if other != donor)
        nearest = {other for _, other in distances[:4]}
        for hydrogen in configuration.positions[
                oxygen_count + 2 * donor:oxygen_count + 2 * donor + 2]:
            direction = _minimum_image(point, hydrogen, configuration.cell)
            acceptor = max(
                nearest,
                key=lambda other: sum(
                    direction[axis] * _minimum_image(
                        point, oxygen[other], configuration.cell)[axis]
                    for axis in range(3)))
            directed_edges.append((donor, acceptor))
    assert len(directed_edges) == 2 * oxygen_count
    assert all(sum(first == donor for first, _ in directed_edges) == 2
               for donor in range(oxygen_count))
    undirected = [tuple(sorted(edge)) for edge in directed_edges]
    assert len(set(undirected)) == 2 * oxygen_count
    assert all(undirected.count(edge) == 1 for edge in set(undirected))


def main() -> None:
    _assert_bernal_fowler(ice_ih())
    _assert_bernal_fowler(ice_ic())
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
