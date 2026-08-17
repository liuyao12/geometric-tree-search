#!/usr/bin/env python3
"""Synthetic leakage, cover, and SE(3) controls for RHS decomposition."""

from types import SimpleNamespace

from materials_gcts_oriented_overlap_ports import IDENTITY, PortAtlas
from materials_gcts_oriented_overlap_ports import ClusterOccurrence
from materials_gcts_partial_promoted_frontier import (
    PartialPromotedCompletion, PredictedMacroChild)
from materials_gcts_port_graph_macros import MacroChildPlacement, MacroEdge
from materials_gcts_partial_macro_components import (
    decompose_atomic_frontier, decompose_partial_macro_completion)


def _rot_z(point):
    return (-point[1], point[0], point[2])


ROT_Z = ((0., -1., 0.), (1., 0., 0.), (0., 0., 1.))
PORT01 = (0, 1, (7,))
PORT11 = (1, 1, (8,))


def _fixture(rotation=IDENTITY, transform=lambda point: point):
    placements = tuple(MacroChildPlacement(
        node, 0 if node == 0 else 1, IDENTITY, (float(node), 0., 0.))
                       for node in range(5))
    macro = SimpleNamespace(
        macro_id=13, child_placements=placements,
        edges=(MacroEdge(0, 1, PORT01), MacroEdge(1, 2, PORT11),
               MacroEdge(0, 3, PORT01)))
    children = []
    for node in (1, 2, 3, 4):
        point = transform((float(node), 0., 0.))
        children.append(PredictedMacroChild(
            node, 1, rotation, point, (("A", point),)))
    completion = PartialPromotedCompletion(
        13, (0,), (20,), tuple(children), rotation, transform((0., 0., 0.)),
        True, False)
    atlas = PortAtlas((), 2, 0, 0, 0, 0,
                      ((0, 1, 0, 1, (7,)), (1, 2, 1, 1, (8,))))
    return SimpleNamespace(atlas=atlas, boundary_ports=(), target_used=False), \
        macro, completion


def test_port_components_and_residual_preserve_complete_cover():
    program, macro, completion = _fixture()
    result = decompose_partial_macro_completion(program, macro, completion)
    assert result.complete_cover and not result.target_used
    assert tuple(item.child_nodes for item in result.emission_components) == \
        ((1,), (3,))
    assert tuple(item.child_nodes for item in result.residual_subclusters) == \
        ((2,), (4,))
    assert result.source_site_count == result.represented_site_count == 4
    assert all(item.exact_proper_se3_candidate
               for item in result.emission_components)


def test_proper_rigid_transform_and_input_edge_permutation_are_invariant():
    first = _fixture()
    second = _fixture(ROT_Z, _rot_z)
    transformed = decompose_partial_macro_completion(*second)
    program, macro, completion = first
    shuffled_macro = SimpleNamespace(
        macro_id=macro.macro_id,
        child_placements=tuple(reversed(macro.child_placements)),
        edges=tuple(reversed(macro.edges)))
    shuffled = decompose_partial_macro_completion(
        program, shuffled_macro, completion)
    original = decompose_partial_macro_completion(*first)
    assert tuple(item.child_nodes for item in transformed.emission_components) == \
        tuple(item.child_nodes for item in original.emission_components)
    assert tuple(item.component_id for item in transformed.emission_components) == \
        tuple(item.component_id for item in original.emission_components)
    assert shuffled.colored_union_digest == original.colored_union_digest


def test_unwitnessed_rhs_edges_do_not_create_emission_actions():
    program, macro, completion = _fixture()
    sealed = SimpleNamespace(atlas=PortAtlas((), 0, 0, 0, 0, 0, ()),
                             boundary_ports=(), target_used=False)
    result = decompose_partial_macro_completion(sealed, macro, completion)
    assert not result.emission_components
    assert len(result.residual_subclusters) == 4
    assert result.complete_cover


def test_target_taint_improper_pose_and_colored_conflict_fail_closed():
    program, macro, completion = _fixture()
    tainted_values = dict(program.__dict__)
    tainted_values["target_used"] = True
    tainted = SimpleNamespace(**tainted_values)
    try:
        decompose_partial_macro_completion(tainted, macro, completion)
    except ValueError as error:
        assert "target-free" in str(error)
    else:
        raise AssertionError("target-tainted decomposition was accepted")
    improper = ((-1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
    bad_pose_values = dict(completion.__dict__)
    bad_pose_values["macro_rotation"] = improper
    bad_pose = SimpleNamespace(**bad_pose_values)
    try:
        decompose_partial_macro_completion(program, macro, bad_pose)
    except ValueError as error:
        assert "proper-SE(3)" in str(error)
    else:
        raise AssertionError("improper pose was accepted")
    children = list(completion.missing_children)
    child_values = dict(children[1].__dict__)
    child_values["sites"] = (("B", (1., 0., 0.)),)
    children[1] = SimpleNamespace(**child_values)
    conflict_values = dict(completion.__dict__)
    conflict_values["missing_children"] = tuple(children)
    conflict = SimpleNamespace(**conflict_values)
    try:
        decompose_partial_macro_completion(program, macro, conflict)
    except ValueError as error:
        assert "colored-site conflict" in str(error)
    else:
        raise AssertionError("colored overlap conflict was accepted")


def test_atomic_frontier_peels_only_the_observed_connected_layer():
    anchor = SimpleNamespace(type_id=0, sites=(("A", (0., 0., 0.)),))
    child_type = SimpleNamespace(type_id=1, sites=tuple(
        ("A", (float(index), 0., 0.)) for index in range(4)))
    program = SimpleNamespace(
        prototypes=(anchor, child_type),
        occurrences=(ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),),
        atlas=PortAtlas((), 1, 0, 0, 0, 0,
                        ((0, 1, 0, 1, (7,)),)),
        boundary_ports=(), target_used=False)
    macro = SimpleNamespace(
        macro_id=21,
        child_placements=(MacroChildPlacement(0, 0, IDENTITY, (0., 0., 0.)),
                          MacroChildPlacement(1, 1, IDENTITY, (0., 0., 0.))),
        edges=(MacroEdge(0, 1, PORT01),), boundary_slots=())
    completion = PartialPromotedCompletion(
        21, (0,), (0,), (PredictedMacroChild(
            1, 1, IDENTITY, (0., 0., 0.), child_type.sites),),
        IDENTITY, (0., 0., 0.), True, False)
    result = decompose_atomic_frontier(program, macro, completion)
    assert result.complete_cover and result.exact_colored_union
    assert len(result.observed_overlap_sites) == 1
    assert tuple(item.prototype_site_indices
                 for item in result.emission_components) == ((1,),)
    assert tuple(item.prototype_site_indices
                 for item in result.residual_subclusters) == ((2, 3),)


if __name__ == "__main__":
    test_port_components_and_residual_preserve_complete_cover()
    test_proper_rigid_transform_and_input_edge_permutation_are_invariant()
    test_unwitnessed_rhs_edges_do_not_create_emission_actions()
    test_target_taint_improper_pose_and_colored_conflict_fail_closed()
    test_atomic_frontier_peels_only_the_observed_connected_layer()
    print("partial macro component tests passed")
