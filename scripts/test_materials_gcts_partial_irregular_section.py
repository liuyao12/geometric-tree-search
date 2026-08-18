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
    false = partial_irregular_section(
        vocabulary, (4,), occupied, species, ((0., 2., 0.),), ("Z",))
    transformed = partial_irregular_section(
        vocabulary, (4,), tuple(_proper(point) for point in reversed(occupied)),
        tuple(reversed(species)), (_proper((0., 1., 0.)),), ("Z",))
    assert exact.minimum_matched_fraction == 1.
    assert exact.minimum_matched_atoms == 3
    assert exact.action_matches[0].training_group_support == 4
    assert false.minimum_matched_fraction == 1 / 3
    assert exact.minimum_matched_fraction == \
        transformed.minimum_matched_fraction
    assert exact.all_searches_exact
    assert not exact.lattice_coordinates_used
    assert not exact.target_used


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
    test_partial_section_rejects_overlap_and_schema_mismatch()
    print("partial irregular-section tests passed")
