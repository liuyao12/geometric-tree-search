#!/usr/bin/env python3
"""Semantic parity checks for sparse-pair dense promotion optimizations."""

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, learn_overlap_ports)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from test_materials_gcts_oriented_overlap_ports import _octahedron
from test_materials_gcts_port_graph_macros import _synthetic_program


def test_allowed_pair_iteration_is_exactly_cartesian_when_pairs_are_all():
    sodium = _octahedron("Na", "Cl")
    chloride = _octahedron("Cl", "Na")
    occurrences = (
        ClusterOccurrence(0, 0, IDENTITY, (0.0, 0.0, 0.0)),
        ClusterOccurrence(1, 1, IDENTITY, (1.0, 0.0, 0.0)),
        ClusterOccurrence(2, 0, IDENTITY, (2.0, 0.0, 0.0)),
    )
    all_ordered_pairs = frozenset(
        (left.occurrence_id, right.occurrence_id)
        for left in occurrences for right in occurrences
        if left.occurrence_id != right.occurrence_id)
    cartesian = learn_overlap_ports(
        (sodium, chloride), occurrences, minimum_overlap=2)
    indexed = learn_overlap_ports(
        (sodium, chloride), occurrences, minimum_overlap=2,
        allowed_occurrence_pairs=all_ordered_pairs)
    assert indexed == cartesian


def test_inverted_support_index_retains_exact_bruteforce_pairs():
    atomic = _synthetic_program()
    mined = mine_port_graph_macros(
        atomic, maximum_nodes=3, geometry_tolerance=1e-6)
    dense = match_dense_macro_types(
        atomic, mined.macro_types, pose_tolerance=1e-6)
    promoted = promote_macro_types(
        atomic, dense.dense_macro_types, pose_tolerance=1e-6,
        minimum_shared_atoms=1)
    supports = dict(promoted.occurrence_supports)
    brute = frozenset(
        (left, right) for left in supports for right in supports
        if left != right and set(supports[left]).intersection(supports[right]))
    atlas_pairs = frozenset(
        (relation[0], relation[1])
        for relation in promoted.atlas.relation_classes)
    assert atlas_pairs == brute


if __name__ == "__main__":
    test_allowed_pair_iteration_is_exactly_cartesian_when_pairs_are_all()
    test_inverted_support_index_retains_exact_bruteforce_pairs()
    print("dense promotion sparse-pair parity: passed")
