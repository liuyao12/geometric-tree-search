#!/usr/bin/env python3

from materials_gcts_irregular_supports import _species_key
from materials_gcts_partial_irregular_port_graph import \
    partial_irregular_port_graph
from materials_gcts_partial_irregular_section import (
    PartialIrregularSection, PartialSupportMatch)


def _section(order=(0, 1)):
    rows = (
        PartialSupportMatch(0, 7, 3, 5, .6, 4, 12, (0, 1, 2)),
        PartialSupportMatch(1, 9, 4, 6, 2 / 3, 5, 13, (0, 1, 3)),
    )
    rows = tuple(rows[index] for index in order)
    rows = tuple(PartialSupportMatch(
        offset, row.prototype_type_id, row.matched_atoms,
        row.prototype_atoms, row.matched_fraction,
        row.training_group_support, row.search_nodes,
        tuple(index if index < 2 else 2 + offset
              for index in row.matched_target_indices))
        for offset, row in enumerate(rows))
    return PartialIrregularSection(
        rows, .6, (0.6 + 2 / 3) / 2, 3, (2,), 2, 2., 2, 1, True)


def _proper(point):
    return (point[1] + 4., point[0] - 2., -point[2] + 7.)


def _reflect(point):
    return (-point[0], point[1], point[2])


def test_typed_port_graph_is_proper_motion_and_action_order_invariant():
    occupied = ((0., 0., 0.), (0., 1., 1.))
    actions = ((1., 0., 0.), (0., 0., 1.))
    base = partial_irregular_port_graph(
        _section(), occupied, ("X", "Y"), actions, ("A", "B"),
        distance_scale=1.)
    transformed = partial_irregular_port_graph(
        _section((1, 0)), tuple(_proper(point) for point in reversed(occupied)),
        ("Y", "X"), tuple(_proper(point) for point in reversed(actions)),
        ("B", "A"), distance_scale=1.)
    reflected = partial_irregular_port_graph(
        _section(), tuple(_reflect(point) for point in occupied),
        ("X", "Y"), tuple(_reflect(point) for point in actions),
        ("A", "B"), distance_scale=1.)
    assert base.canonical_digest == transformed.canonical_digest
    assert base.edges[0].chirality in (-1, 1)
    assert reflected.edges[0].chirality == -base.edges[0].chirality
    assert base.canonical_digest != reflected.canonical_digest
    assert base.nodes[0].action_species in (_species_key("A"),
                                            _species_key("B"))
    assert base.isolated_nodes == 0
    assert base.proper_se3_invariant
    assert not base.lattice_coordinates_used
    assert not base.target_used


def test_port_graph_rejects_schema_mismatch():
    try:
        partial_irregular_port_graph(
            _section(), ((0., 0., 0.),), ("X",), ((1., 0., 0.),),
            ("A",), distance_scale=1.)
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched action graph was accepted")


if __name__ == "__main__":
    test_typed_port_graph_is_proper_motion_and_action_order_invariant()
    test_port_graph_rejects_schema_mismatch()
    print("partial irregular-port graph tests passed")
