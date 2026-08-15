#!/usr/bin/env python3

from dataclasses import replace
from types import SimpleNamespace

from materials_gcts_macro_stationary_adapter import (
    adapt_macro_type, prototype_semantics)
from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, OrientedOverlapPort, PortAtlas,
    make_prototype)
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_recursive_port_hierarchy import (
    drive_recursive_port_hierarchy, real_first_level_callbacks)


def _synthetic_program():
    prototype = make_prototype(0, (
        ("Na", (0., 0., 0.)), ("Na", (.2, 0., 0.)),
        ("Cl", (0., .3, 0.)), ("Yb", (0., 0., .4))))
    translations = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.),
                    (0., 10., 0.), (1., 10., 0.), (0., 11., 0.))
    occurrences = tuple(ClusterOccurrence(
        index, 0, IDENTITY, translation)
        for index, translation in enumerate(translations))
    x_key = (101,)
    y_key = (202,)
    diagonal_key = (303,)
    x_port = OrientedOverlapPort(
        0, 0, IDENTITY, (1., 0., 0.), ((1, 0),), ("Na",),
        x_key, 2)
    y_port = OrientedOverlapPort(
        0, 0, IDENTITY, (0., 1., 0.), ((2, 0),), ("Cl",),
        y_key, 2)
    diagonal = OrientedOverlapPort(
        0, 0, IDENTITY, (-1., 1., 0.), (), (), diagonal_key, 2)
    relations = []
    for offset in (0, 3):
        relations.extend((
            (offset, offset + 1, 0, 0, x_key),
            (offset, offset + 2, 0, 0, y_key),
            (offset + 1, offset + 2, 0, 0, diagonal_key)))
    atlas = PortAtlas(
        (x_port, y_port, diagonal), len(relations), 0, 0, 0, 0,
        tuple(relations))
    supports = (
        (0, (0, 1, 2, 3)), (1, (1, 4, 5, 6)),
        (2, (4, 7, 8, 9)),
        (3, (20, 21, 22, 23)), (4, (21, 24, 25, 26)),
        (5, (24, 27, 28, 29)))
    return SimpleNamespace(
        prototypes=(prototype,), occurrences=occurrences,
        occurrence_supports=supports, atlas=atlas,
        minimum_shared_atoms=1, minimum_distance=1.0,
        family_label_used=False, lattice_used=False,
        physical_potential_used=False, target_used=False)


def _three_node_macro(program):
    mined = mine_port_graph_macros(
        program, maximum_nodes=3, geometry_tolerance=1e-6)
    return next(item for item in mined.macro_types
                if len(item.node_types) == 3 and len(item.edges) >= 2)


def test_real_atlas_ports_resolve_to_chemical_stationary_semantics():
    program = _synthetic_program()
    adapted = adapt_macro_type(program, _three_node_macro(program))
    assert adapted.leakage_clean
    assert adapted.resolved_port_classes >= 1
    assert adapted.child_prototype_types == 1
    assert adapted.canonical.normalized_key
    assert all("builtins.str:'Na'*2" in child.chemistry_key
               for child in adapted.production.children)
    assert all(population == (("builtins.str:'Cl'", 1),
                              ("builtins.str:'Na'", 2),
                              ("builtins.str:'Yb'", 1))
               for population in adapted.child_chemical_populations)
    assert all(child.chirality_key for child in adapted.production.children)
    assert all(port.overlap_chemistry in (
        ("builtins.str:'Na'*1",),
        ("builtins.str:'Cl'*1",), ())
               for port in adapted.production.internal_ports)
    assert all(port.port_key[0] == "colored-overlap"
               for port in adapted.production.internal_ports)


def test_raw_unadmitted_pose_key_cannot_define_a_semantic_port():
    program = _synthetic_program()
    macro = _three_node_macro(program)
    edge = macro.edges[0]
    broken_edge = replace(
        edge, port=(edge.port[0], edge.port[1], (999999,)))
    broken = replace(macro, edges=(broken_edge,) + macro.edges[1:])
    try:
        adapt_macro_type(program, broken)
    except ValueError as error:
        assert "not admitted" in str(error)
    else:
        raise AssertionError("an unadmitted raw pose key was accepted")


def test_prototype_chirality_uses_only_proper_frames():
    original = make_prototype(0, (
        ("A", (0., 0., 0.)), ("B", (1., 0., 0.)),
        ("C", (0., 2., 0.)), ("D", (.2, .3, 3.))))
    mirrored = make_prototype(1, tuple(
        (species, (-point[0], point[1], point[2]))
        for species, point in original.sites))
    left = prototype_semantics(original)
    right = prototype_semantics(mirrored)
    assert left.chemistry_key == right.chemistry_key
    assert left.chirality_key != right.chirality_key


def test_chemistry_role_reduces_stoichiometry_but_retains_population_audit():
    small = make_prototype(0, (
        ("Na", (0., 0., 0.)), ("Cl", (1., 0., 0.)),
        ("Na", (0., 1., 0.)), ("Cl", (0., 0., 1.))))
    large = make_prototype(1, (
        ("Na", (0., 0., 0.)), ("Cl", (1., 0., 0.)),
        ("Na", (0., 1., 0.)), ("Cl", (0., 0., 1.)),
        ("Na", (2., 0., 0.)), ("Cl", (0., 2., 0.)),
        ("Na", (0., 0., 2.)), ("Cl", (2., 2., 2.))))
    left = prototype_semantics(small)
    right = prototype_semantics(large)
    assert left.chemistry_key == right.chemistry_key
    assert left.chemical_population != right.chemical_population


def test_recursive_driver_marks_only_adapter_certified_semantics():
    hierarchy = drive_recursive_port_hierarchy(
        _synthetic_program(), real_first_level_callbacks(maximum_nodes=3),
        maximum_levels=2)
    assert hierarchy.levels[0].certified_stationarity_signatures
    # A semantic key is safe to compare; it is not itself evidence that an
    # adjacent scale repeats. This finite example provides no such witness.
    assert not hierarchy.stationary_witnesses


if __name__ == "__main__":
    test_real_atlas_ports_resolve_to_chemical_stationary_semantics()
    test_raw_unadmitted_pose_key_cannot_define_a_semantic_port()
    test_prototype_chirality_uses_only_proper_frames()
    test_chemistry_role_reduces_stoichiometry_but_retains_population_audit()
    test_recursive_driver_marks_only_adapter_certified_semantics()
    print("real macro atlas stationary adapter: all assertions passed")
