#!/usr/bin/env python3
"""Adversarial contracts for partial frozen-child site accumulation."""

from dataclasses import replace
from types import SimpleNamespace

from materials_gcts_oriented_overlap_ports import (
    IDENTITY, PortAtlas, make_prototype)
from materials_gcts_partial_promoted_frontier import PartialPromotedCompletion
from materials_gcts_port_graph_macros import MacroChildPlacement, MacroEdge
from materials_gcts_partial_site_accumulation import (
    apply_site_fragment, freeze_site_fragment,
    initialize_partial_site_accumulation)


def _fixture():
    prototypes = (
        SimpleNamespace(type_id=0, sites=(("A", (0., 0., 0.)),)),
        SimpleNamespace(type_id=1, sites=(
            ("A", (1., 0., 0.)), ("B", (1., 1., 0.)))),
        SimpleNamespace(type_id=2, sites=(
            ("B", (1., 1., 0.)), ("C", (0., 1., 0.)))))
    ports = ((0, 1, (7,)), (1, 2, (8,)))
    program = SimpleNamespace(
        prototypes=prototypes, target_used=False, boundary_ports=(),
        atlas=PortAtlas((), 2, 0, 0, 0, 0,
                        ((0, 1, *ports[0]), (1, 2, *ports[1]))))
    macro = SimpleNamespace(
        macro_id=9,
        child_placements=tuple(MacroChildPlacement(
            node, node, IDENTITY, (0., 0., 0.)) for node in range(3)),
        edges=(MacroEdge(0, 1, ports[0]), MacroEdge(1, 2, ports[1])))
    completion = PartialPromotedCompletion(
        9, (0,), (0,), (), IDENTITY, (0., 0., 0.), True, False)
    # Exact promoted support has three noncollinear sites and shared B once.
    parent = make_prototype(20, (
        ("A", (0., 0., 0.)), ("A", (1., 0., 0.)),
        ("B", (1., 1., 0.)), ("C", (0., 1., 0.))))
    # Completion metadata must list missing children; their exact rendered
    # sites are checked from the frozen prototypes, not trusted here.
    completion = replace(completion, missing_children=tuple(
        SimpleNamespace(node=node, type_id=node, rotation=IDENTITY,
                        translation=(0., 0., 0.), sites=prototypes[node].sites)
        for node in (1, 2)))
    return program, macro, completion, parent


def test_partial_atoms_never_certify_a_whole_child_or_parent():
    program, macro, completion, parent = _fixture()
    state = initialize_partial_site_accumulation(
        program, macro, completion, (("A", (0., 0., 0.)),),
        promoted_prototype=parent, pose_tolerance=1e-6)
    fragment = freeze_site_fragment(
        state, 1, (("A", (1., 0., 0.)),))
    state = apply_site_fragment(state, fragment)
    children = {item.child_node: item for item in state.child_certificates}
    assert not children[1].occurrence_admissible
    assert not state.parent_certificate.promoted_parent_admissible
    assert len(state.residual_terminals) == 2


def test_shared_site_has_multiple_owners_and_completes_both_obligations():
    program, macro, completion, parent = _fixture()
    state = initialize_partial_site_accumulation(
        program, macro, completion, (("A", (0., 0., 0.)),),
        promoted_prototype=parent, pose_tolerance=1e-6)
    owners = dict(state.shared_site_owners)
    shared = next(key for key, value in owners.items() if value == (1, 2))
    state = apply_site_fragment(state, freeze_site_fragment(
        state, 1, (("A", (1., 0., 0.)),
                   ("B", (1., 1., 0.)))))
    children = {item.child_node: item for item in state.child_certificates}
    assert children[1].occurrence_admissible
    assert not children[2].occurrence_admissible
    assert shared in state.satisfied_site_keys
    state = apply_site_fragment(state, freeze_site_fragment(
        state, 2, (("C", (0., 1., 0.)),)))
    assert all(item.occurrence_admissible for item in state.child_certificates)
    assert not state.residual_terminals
    assert state.parent_certificate.promoted_parent_admissible


def test_unsupported_forged_redundant_and_target_fragments_fail_closed():
    program, macro, completion, parent = _fixture()
    state = initialize_partial_site_accumulation(
        program, macro, completion, (("A", (0., 0., 0.)),),
        promoted_prototype=parent, pose_tolerance=1e-6)
    try:
        freeze_site_fragment(state, 1, (("X", (9., 9., 9.)),))
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported site became a fragment")
    good = freeze_site_fragment(state, 1, (("A", (1., 0., 0.)),))
    try:
        apply_site_fragment(state, replace(good, fragment_id="forged"))
    except ValueError:
        pass
    else:
        raise AssertionError("forged fragment digest was accepted")
    state = apply_site_fragment(state, good)
    try:
        apply_site_fragment(state, good)
    except ValueError:
        pass
    else:
        raise AssertionError("redundant fragment was accepted")
    try:
        apply_site_fragment(state, replace(good, target_used=True))
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted fragment was accepted")


def test_parent_needs_frozen_ports_and_an_exact_promoted_fit():
    program, macro, completion, parent = _fixture()
    full_sites = (("A", (0., 0., 0.)), ("A", (1., 0., 0.)),
                  ("B", (1., 1., 0.)), ("C", (0., 1., 0.)))
    no_ports = SimpleNamespace(**{**program.__dict__,
                                  "atlas": PortAtlas((), 0, 0, 0, 0, 0, ())})
    state = initialize_partial_site_accumulation(
        no_ports, macro, completion, full_sites,
        promoted_prototype=parent, pose_tolerance=1e-6)
    assert all(item.occurrence_admissible for item in state.child_certificates)
    assert not state.parent_certificate.frozen_ports_verified
    assert not state.parent_certificate.promoted_parent_admissible
    state = initialize_partial_site_accumulation(
        program, macro, completion, full_sites,
        promoted_prototype=None, pose_tolerance=1e-6)
    assert not state.parent_certificate.promoted_prototype_fit_verified
    assert not state.parent_certificate.promoted_parent_admissible


def test_claimed_exact_completion_cannot_override_frozen_child_geometry():
    program, macro, completion, parent = _fixture()
    children = list(completion.missing_children)
    children[0] = SimpleNamespace(
        **{**children[0].__dict__, "sites": (("X", (9., 9., 9.)),)})
    poisoned = replace(completion, missing_children=tuple(children))
    try:
        initialize_partial_site_accumulation(
            program, macro, poisoned, (("A", (0., 0., 0.)),),
            promoted_prototype=parent, pose_tolerance=1e-6)
    except ValueError as error:
        assert "differs from frozen RHS" in str(error)
    else:
        raise AssertionError("claimed exact child geometry was trusted")


if __name__ == "__main__":
    test_partial_atoms_never_certify_a_whole_child_or_parent()
    test_shared_site_has_multiple_owners_and_completes_both_obligations()
    test_unsupported_forged_redundant_and_target_fragments_fail_closed()
    test_parent_needs_frozen_ports_and_an_exact_promoted_fit()
    test_claimed_exact_completion_cannot_override_frozen_child_geometry()
    print("partial site accumulation contracts passed")
