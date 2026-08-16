#!/usr/bin/env python3
"""Exact and adversarial controls for partial promoted recognition."""

from types import SimpleNamespace

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, ClusterPrototype, IDENTITY, make_prototype)
from materials_gcts_port_graph_macros import (
    BoundarySlot, MacroChildPlacement, MacroEdge)
from materials_gcts_oriented_overlap_ports import PortAtlas
from materials_gcts_partial_promoted_frontier import (
    enumerate_partial_promoted_completions)


def _fixture(second_translation=(2., 0., 0.)):
    prototype = make_prototype(0, (
        ("A", (0., 0., 0.)), ("B", (.4, 0., 0.)),
        ("C", (0., .6, 0.))))
    second_prototype = make_prototype(1, (
        ("D", (0., 0., 0.)), ("E", (.4, 0., 0.)),
        ("F", (0., .6, 0.))))
    occurrences = (
        ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),
        ClusterOccurrence(1, 1, IDENTITY, second_translation))
    program = SimpleNamespace(
        prototypes=(prototype, second_prototype), occurrences=occurrences,
        minimum_distance=.4)
    macro = SimpleNamespace(macro_id=7, child_placements=(
        MacroChildPlacement(0, 0, IDENTITY, (0., 0., 0.)),
        MacroChildPlacement(1, 1, IDENTITY, (2., 0., 0.)),
        MacroChildPlacement(2, 0, IDENTITY, (4., 0., 0.))))
    return program, macro


def test_two_exact_children_predict_missing_frozen_rhs_child():
    program, macro = _fixture()
    result = enumerate_partial_promoted_completions(program, (macro,))
    assert not result.target_used and result.proper_se3_only
    assert len(result.completions) == 1
    completion = result.completions[0]
    assert completion.macro_id == 7
    assert completion.matched_nodes == (0, 1)
    assert len(completion.missing_children) == 1
    assert completion.missing_children[0].translation == (4., 0., 0.)


def test_one_or_inconsistent_child_cannot_complete():
    program, macro = _fixture((3., 0., 0.))
    assert not enumerate_partial_promoted_completions(
        program, (macro,)).completions
    one = SimpleNamespace(
        prototypes=program.prototypes, occurrences=program.occurrences[:1],
        minimum_distance=program.minimum_distance)
    assert not enumerate_partial_promoted_completions(
        one, (macro,)).completions


def test_collision_and_cross_type_ambiguity_fail_closed():
    program, macro = _fixture()
    predicted = enumerate_partial_promoted_completions(program, (macro,))
    conflict_point = predicted.completions[0].missing_children[0].sites[0][1]
    collision = enumerate_partial_promoted_completions(
        program, (macro,), explicit_seed_sites=(("X", conflict_point),))
    assert not collision.completions and collision.collision_rejections > 0
    alias = SimpleNamespace(macro_id=8,
                            child_placements=macro.child_placements)
    ambiguous = enumerate_partial_promoted_completions(
        program, (macro, alias))
    assert ambiguous.ambiguous_completion_signatures == 1
    assert not ambiguous.completions


def test_target_tainted_seed_is_rejected():
    program, macro = _fixture()
    tainted = SimpleNamespace(
        prototypes=program.prototypes, occurrences=program.occurrences,
        minimum_distance=program.minimum_distance, target_used=True)
    try:
        enumerate_partial_promoted_completions(tainted, (macro,))
    except ValueError as error:
        assert "sealed seed" in str(error)
    else:
        raise AssertionError("target-tainted seed was accepted")


def test_full_macro_requires_its_frozen_internal_port_relation():
    program, macro = _fixture()
    macro = SimpleNamespace(
        macro_id=macro.macro_id, child_placements=macro.child_placements,
        edges=(MacroEdge(0, 1, (0, 1, (9,))),
               MacroEdge(1, 2, (1, 0, (10,)))))
    missing = SimpleNamespace(
        **program.__dict__, atlas=PortAtlas((), 0, 0, 0, 0, 0, ()))
    rejected = enumerate_partial_promoted_completions(missing, (macro,))
    assert not rejected.completions
    assert rejected.internal_port_rejections > 0
    admitted = SimpleNamespace(
        **program.__dict__, atlas=PortAtlas(
            (), 1, 0, 0, 0, 0, ((0, 1, 0, 1, (9,)),)))
    accepted = enumerate_partial_promoted_completions(admitted, (macro,))
    assert len(accepted.completions) == 1


def test_one_child_has_finite_frozen_port_completion_set():
    program, macro = _fixture()
    one_child = SimpleNamespace(
        prototypes=program.prototypes, occurrences=program.occurrences[:1],
        minimum_distance=program.minimum_distance,
        atlas=SimpleNamespace(ports=(SimpleNamespace(
            parent_type=0, child_type=1, symmetry_orbit_key=(9,)),),
                              relation_classes=()))
    binary = SimpleNamespace(
        macro_id=7, child_placements=macro.child_placements[:2],
        edges=(MacroEdge(0, 1, (0, 1, (9,))),))
    result = enumerate_partial_promoted_completions(
        one_child, (binary,), minimum_matched_children=1,
        minimum_child_coverage=.5)
    assert len(result.completions) == 1
    assert result.completions[0].matched_nodes == (0,)
    assert len(result.completions[0].missing_children) == 1
    assert result.frame_hypotheses == len(
        program.prototypes[0].proper_symmetries)
    outside = enumerate_partial_promoted_completions(
        one_child, (binary,), minimum_matched_children=1,
        minimum_child_coverage=.5,
        public_boundary=SimpleNamespace(
            origin=(0., 0., 0.), outer_radius=1.))
    assert not outside.completions
    assert outside.public_boundary_rejections > 0
    blocked = SimpleNamespace(
        prototypes=one_child.prototypes, occurrences=one_child.occurrences,
        minimum_distance=one_child.minimum_distance,
        atlas=SimpleNamespace(ports=(), relation_classes=()))
    rejected = enumerate_partial_promoted_completions(
        blocked, (binary,), minimum_matched_children=1,
        minimum_child_coverage=.5)
    assert not rejected.completions
    assert rejected.one_child_missing_port_rejections > 0


def test_one_child_rejects_continuous_collinear_frame_and_no_edge():
    program, macro = _fixture()
    collinear = ClusterPrototype(0, (
        ("A", (-1., 0., 0.)), ("B", (0., 0., 0.)),
        ("C", (1., 0., 0.))), (IDENTITY,))
    bad = SimpleNamespace(
        prototypes=(collinear, program.prototypes[1]),
        occurrences=program.occurrences[:1], minimum_distance=.4,
        atlas=SimpleNamespace(ports=(SimpleNamespace(
            parent_type=0, child_type=1, symmetry_orbit_key=(9,)),),
                              relation_classes=()))
    binary = SimpleNamespace(
        macro_id=7, child_placements=macro.child_placements[:2],
        edges=(MacroEdge(0, 1, (0, 1, (9,))),))
    rejected = enumerate_partial_promoted_completions(
        bad, (binary,), minimum_matched_children=1)
    assert not rejected.completions
    no_edge = SimpleNamespace(
        macro_id=7, child_placements=macro.child_placements[:2], edges=())
    rejected = enumerate_partial_promoted_completions(
        SimpleNamespace(
            prototypes=program.prototypes, occurrences=program.occurrences[:1],
            minimum_distance=program.minimum_distance, atlas=bad.atlas),
        (no_edge,),
        minimum_matched_children=1)
    assert not rejected.completions
    assert rejected.one_child_missing_port_rejections > 0


def test_every_finite_symmetry_gauge_is_enumerated_and_boundary_can_witness():
    anchor = make_prototype(0, (
        ("A", (1., 0., 0.)), ("A", (-.5, .8660254038, 0.)),
        ("A", (-.5, -.8660254038, 0.))))
    child = make_prototype(1, (
        ("D", (0., 0., 0.)), ("E", (.4, 0., 0.)),
        ("F", (0., .6, 0.))))
    key = (0, 1, (12,))
    program = SimpleNamespace(
        prototypes=(anchor, child),
        occurrences=(ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),),
        minimum_distance=.4,
        atlas=SimpleNamespace(ports=(SimpleNamespace(
            parent_type=0, child_type=1, symmetry_orbit_key=(12,)),),
                              relation_classes=()))
    macro = SimpleNamespace(
        macro_id=9, child_placements=(
            MacroChildPlacement(0, 0, IDENTITY, (0., 0., 0.)),
            MacroChildPlacement(1, 1, IDENTITY, (5., 0., 0.))),
        edges=(), boundary_slots=(
            BoundarySlot(0, "outgoing", 1, key, 3, 1.),))
    result = enumerate_partial_promoted_completions(
        program, (macro,), minimum_matched_children=1)
    assert len(anchor.proper_symmetries) > 1
    assert result.frame_hypotheses == len(anchor.proper_symmetries)
    assert len(result.completions) == len(anchor.proper_symmetries)


if __name__ == "__main__":
    test_two_exact_children_predict_missing_frozen_rhs_child()
    test_one_or_inconsistent_child_cannot_complete()
    test_collision_and_cross_type_ambiguity_fail_closed()
    test_target_tainted_seed_is_rejected()
    test_full_macro_requires_its_frozen_internal_port_relation()
    test_one_child_has_finite_frozen_port_completion_set()
    test_one_child_rejects_continuous_collinear_frame_and_no_edge()
    test_every_finite_symmetry_gauge_is_enumerated_and_boundary_can_witness()
    print("partial promoted frontier: all assertions passed")
