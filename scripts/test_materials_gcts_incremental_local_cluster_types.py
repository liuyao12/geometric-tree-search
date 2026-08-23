"""Exact parity checks for incremental off-lattice local cluster colors."""

from materials_gcts_recursive_connections import (
    LocalClusterType, extend_local_cluster_types, local_cluster_types,
    map_to_prototypes)


def test_incremental_types_match_full_recompute_for_existing_species():
    positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.),
                 (0., 0., 1.), (2., 0., 0.))
    colors = ("A", "B", "A", "B", "A")
    edges = (.75, 1.1, 2.2)
    prior = local_cluster_types(positions, colors, edges)
    added_positions = ((1., 1., 0.), (-.5, 0., 0.))
    added_colors = ("B", "A")
    incremental = extend_local_cluster_types(
        positions, colors, prior, added_positions, added_colors, edges)
    full = local_cluster_types(
        positions + added_positions, colors + added_colors, edges)
    assert incremental == full


def test_incremental_types_fall_back_when_a_new_species_appears():
    positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    colors = ("A", "B", "A")
    edges = (1.1, 2.)
    prior = local_cluster_types(positions, colors, edges)
    incremental = extend_local_cluster_types(
        positions, colors, prior, ((0., 0., 1.),), ("C",), edges)
    full = local_cluster_types(
        positions + ((0., 0., 1.),), colors + ("C",), edges)
    assert incremental == full


def test_prototype_mapping_cache_is_exact_and_reusable():
    positions = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.),
                 (0., 0., 1.), (2., 0., 0.))
    colors = ("A", "B", "A", "B", "A")
    rows = local_cluster_types(positions, colors, (.75, 1.1, 2.2))
    prototypes = tuple(sorted(set(rows)))
    expected = map_to_prototypes(rows, prototypes)
    cache = {}
    first = map_to_prototypes(rows, prototypes, cache)
    populated = dict(cache)
    second = map_to_prototypes(tuple(reversed(rows)), prototypes, cache)
    assert first == expected
    assert second == tuple(reversed(expected))
    assert cache == populated
    extra = LocalClusterType(
        prototypes[0].color_key,
        tuple(value + 100
              for value in prototypes[0].cumulative_neighbor_counts))
    map_to_prototypes(rows, prototypes + (extra,), cache)
    assert len(cache) == 2


if __name__ == "__main__":
    test_incremental_types_match_full_recompute_for_existing_species()
    test_incremental_types_fall_back_when_a_new_species_appears()
    test_prototype_mapping_cache_is_exact_and_reusable()
    print("incremental local cluster types: passed")
