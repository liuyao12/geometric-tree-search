#!/usr/bin/env python3

from materials_gcts_irregular_supports import (
    FrozenSupportPrototype, FrozenSupportVocabulary, _species_key)
from materials_gcts_partial_irregular_section import partial_irregular_section


def _prototype():
    species = tuple(_species_key(item) for item in ("X", "Y", "Z"))
    matrix = ((0, 100, 100), (100, 0, 141), (100, 141, 0))
    signature = tuple(sorted((species[index], tuple(sorted(
        (species[other], matrix[index][other]) for other in range(3)
        if other != index))) for index in range(3)))
    prototype = FrozenSupportPrototype(7, 1, species, matrix, signature)
    return FrozenSupportVocabulary((prototype,), .01, 1, 3, .1, 8)


def _proper(point):
    return (point[1] + 4., point[0] - 2., -point[2] + 7.)


def test_partial_section_detects_target_free_cluster_completion():
    vocabulary = _prototype()
    occupied = ((0., 0., 0.), (1., 0., 0.))
    species = ("X", "Y")
    exact = partial_irregular_section(
        vocabulary, (4,), occupied, species, ((0., 1., 0.),), ("Z",))
    uncached = partial_irregular_section(
        vocabulary, (4,), occupied, species, ((0., 1., 0.),), ("Z",),
        use_distance_cache=False)
    false = partial_irregular_section(
        vocabulary, (4,), occupied, species, ((0., 2., 0.),), ("Z",))
    transformed = partial_irregular_section(
        vocabulary, (4,), tuple(_proper(point) for point in reversed(occupied)),
        tuple(reversed(species)), (_proper((0., 1., 0.)),), ("Z",))
    assert exact.minimum_matched_fraction == 1.
    assert exact == uncached
    assert exact.minimum_matched_atoms == 3
    assert exact.action_matches[0].training_group_support == 4
    assert exact.action_matches[0].matched_target_indices == (0, 1, 2)
    assert false.minimum_matched_fraction == 1 / 3
    assert exact.minimum_matched_fraction == \
        transformed.minimum_matched_fraction
    assert exact.all_searches_exact
    assert not exact.lattice_coordinates_used
    assert not exact.target_used


def test_partial_section_exposes_only_aggregated_support_incidence():
    row = partial_irregular_section(
        _prototype(), (4,), ((0., 0., 0.),), ("X",),
        ((1., 0., 0.), (0., 1., 0.)), ("Y", "Z"))
    assert row.pair_shared_occupied_atoms == (1,)
    assert row.minimum_pair_shared_occupied == 1
    assert row.mean_pair_shared_occupied == 1.
    assert row.maximum_pair_shared_occupied == 1
    assert row.connected_action_pairs == 1


def test_partial_section_rejects_overlap_and_schema_mismatch():
    vocabulary = _prototype()
    invalid = (
        (((0., 0., 0.),), ("X",), ((0., 0., 0.),), ("Z",), (4,)),
        (((0., 0., 0.),), ("X",), ((0., 1., 0.),), ("Q",), (4,)),
    )
    for occupied, species, actions, colors, support in invalid:
        try:
            partial_irregular_section(
                vocabulary, support, occupied, species, actions, colors)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid partial section was accepted")


if __name__ == "__main__":
    test_partial_section_detects_target_free_cluster_completion()
    test_partial_section_exposes_only_aggregated_support_incidence()
    test_partial_section_rejects_overlap_and_schema_mismatch()
    print("partial irregular-section tests passed")
