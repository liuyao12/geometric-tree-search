#!/usr/bin/env python3

from materials_gcts_spatial_support_hierarchy import (
    guarded_octants, learn_spatial_support_hierarchy)


def test_recursive_supports_are_exact_disjoint_covers() -> None:
    positions = tuple(
        (float(x), float(y), float(z))
        for x in (-3, -2, -1, 1, 2, 3)
        for y in (-3, -2, -1, 1, 2, 3)
        for z in (-3, -2, -1, 1, 2, 3))
    species = tuple("A" if round(sum(point)) % 2 else "B"
                    for point in positions)
    domains = guarded_octants(positions, margin=.1)
    result = learn_spatial_support_hierarchy(
        positions, species, domains, radius_scales=(.5, 1.1, 2.1))
    assert result.assigned_atoms == len(positions)
    assert result.domains == 8
    assert result.complete_cover_each_level
    assert result.rigid_motion_invariant
    assert not result.construction_order_used
    assert all(level.exact_child_cover for level in result.levels)
    moved_positions = tuple((-point[1] + 4.25, point[0] - 2.5,
                             point[2] + .75)
                            for point in reversed(positions))
    moved_species = tuple(reversed(species))
    moved = learn_spatial_support_hierarchy(
        moved_positions, moved_species,
        guarded_octants(moved_positions, margin=.1),
        radius_scales=(.5, 1.1, 2.1))
    summary = lambda hierarchy: tuple(
        (level.geometry_types, level.recurrent_types,
         level.largest_recurrent_support, level.recurrent_atom_coverage)
        for level in hierarchy.levels)
    assert summary(moved) == summary(result)


if __name__ == "__main__":
    test_recursive_supports_are_exact_disjoint_covers()
    print("generic spatial support hierarchy: all assertions passed")
