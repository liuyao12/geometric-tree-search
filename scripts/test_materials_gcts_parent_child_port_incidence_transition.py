#!/usr/bin/env python3
"""Focused invariance tests for parent→child typed incidence."""

import math

from materials_gcts_irregular_supports import (
    FrozenSupportPrototype, FrozenSupportVocabulary, _metric_signature,
    _species_key)
from materials_gcts_parent_child_port_incidence_transition import (
    parent_child_port_incidence_transition)


def _rotate(point):
    # Proper signed-coordinate rotation followed by translation.
    return (point[1] + 7., -point[0] - 3., point[2] + 11.)


def _vocabulary():
    species = (_species_key("X"), _species_key("Y"), _species_key("X"))
    table = ((0, 10, 10), (10, 0, 14), (10, 14, 0))
    signature = _metric_signature(range(3), species,
                                  ((0., 1., 1.), (1., 0., math.sqrt(2.)),
                                   (1., math.sqrt(2.), 0.)), .1)
    prototype = FrozenSupportPrototype(91, 1, species, table, signature)
    return FrozenSupportVocabulary((prototype,), .1, 1, 3, .2, 3)


def test_incidence_is_permutation_and_proper_motion_invariant():
    vocabulary = _vocabulary()
    occupied = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
    colors = ("X", "Y", "X")
    parent = ((0., 0., 1.), (1., 0., 1.), (0., 1., 1.))
    child = ((0., 0., 2.), (1., 0., 2.), (0., 1., 2.))
    child_occupied = occupied + parent
    child_colors = colors + colors
    first = parent_child_port_incidence_transition(
        vocabulary, (4,), occupied, colors, parent, colors,
        child_occupied, child_colors, child, colors, distance_scale=1.)
    permutation = (2, 0, 1)
    second = parent_child_port_incidence_transition(
        vocabulary, (4,), tuple(_rotate(point) for point in occupied), colors,
        tuple(_rotate(parent[index]) for index in permutation),
        tuple(colors[index] for index in permutation),
        tuple(_rotate(point) for point in child_occupied), child_colors,
        tuple(_rotate(child[index]) for index in permutation),
        tuple(colors[index] for index in permutation), distance_scale=1.)
    assert first.canonical_digest == second.canonical_digest
    assert first.nodes == second.nodes
    assert first.incidence_edges == second.incidence_edges
    assert len(first.nodes) == 6
    assert len(first.incidence_edges) == 15
    assert all(node.support_type_id == 0 for node in first.nodes)
    assert first.target_used is False
    assert first.lattice_coordinates_used is False


if __name__ == "__main__":
    test_incidence_is_permutation_and_proper_motion_invariant()
    print("parent-child port-incidence transition tests passed")
