#!/usr/bin/env python3

from materials_gcts_grouped_irregular_vocabulary import (
    fit_grouped_irregular_vocabulary, merge_grouped_vocabulary)
from materials_gcts_irregular_supports import (
    FrozenSupportPrototype, FrozenSupportVocabulary, _species_key)


def _prototype(type_id, edges):
    species = tuple(_species_key("X") for _ in range(6))
    matrix = tuple(tuple(0 if left == right else
                         1 if tuple(sorted((left, right))) in edges else 2
                         for right in range(6)) for left in range(6))
    signature = tuple(sorted((species[index], tuple(sorted(
        (species[other], matrix[index][other]) for other in range(6)
        if other != index))) for index in range(6)))
    return FrozenSupportPrototype(type_id, 1, species, matrix, signature)


def _vocabulary(*prototypes):
    return FrozenSupportVocabulary(tuple(prototypes), .01, 2, 8, .1, 20)


def test_group_votes_are_independent_and_homometric_classes_split():
    cycle = frozenset(tuple(sorted(edge)) for edge in
                      ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)))
    triangles = frozenset(tuple(sorted(edge)) for edge in
                          ((0, 1), (1, 2), (2, 0),
                           (3, 4), (4, 5), (5, 3)))
    a0, a1, a2 = (_prototype(index, cycle) for index in range(3))
    b0, b1 = (_prototype(10 + index, triangles) for index in range(2))
    merged = merge_grouped_vocabulary(
        (_vocabulary(a0, a1, b0), _vocabulary(a2, b1)), (.8, .9),
        minimum_group_support=2)
    assert merged.input_prototype_count == 5
    assert merged.recurrent_prototype_count == 2
    assert merged.training_group_support == (2, 2)
    assert all(row.type_id == index for index, row in
               enumerate(merged.vocabulary.prototypes))
    assert not merged.lattice_coordinates_used
    assert not merged.target_used

    try:
        merge_grouped_vocabulary(
            (_vocabulary(a0, a1), _vocabulary(a2)), (.8, .9),
            minimum_group_support=3)
    except ValueError:
        pass
    else:
        raise AssertionError("impossible group support was accepted")


def test_group_order_does_not_change_scientific_vocabulary():
    cycle = frozenset(tuple(sorted(edge)) for edge in
                      ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)))
    first = _vocabulary(_prototype(7, cycle))
    second = _vocabulary(_prototype(99, cycle))
    left = merge_grouped_vocabulary((first, second), (.7, .9),
                                    minimum_group_support=2)
    right = merge_grouped_vocabulary((second, first), (.9, .7),
                                     minimum_group_support=2)
    assert left.training_group_support == right.training_group_support == (2,)
    assert left.vocabulary.prototypes[0].signature == \
        right.vocabulary.prototypes[0].signature


def test_end_to_end_group_fit_is_proper_motion_invariant():
    first = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.),
             (10., 0., 0.), (11., 0., 0.), (10., 1., 0.))
    second = tuple((point[1] + 3., point[0] - 4., -point[2] + 2.)
                   for point in first)
    species = ("X", "Y", "Z", "X", "Y", "Z")
    grouped, covers = fit_grouped_irregular_vocabulary(
        ((species, first), (species, second)), minimum_group_support=2,
        minimum_neighbors=2, maximum_neighbors=3,
        maximum_merged_size=8)
    assert grouped.recurrent_prototype_count >= 1
    assert all(value == 2 for value in grouped.training_group_support)
    assert all(cover.complete and cover.repeated_coverage == 1.
               for cover in covers)


if __name__ == "__main__":
    test_group_votes_are_independent_and_homometric_classes_split()
    test_group_order_does_not_change_scientific_vocabulary()
    test_end_to_end_group_fit_is_proper_motion_invariant()
    print("grouped irregular-vocabulary tests passed")
