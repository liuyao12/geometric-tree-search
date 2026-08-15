#!/usr/bin/env python3

import math

from materials_gcts_oriented_overlap_ports import IDENTITY, matmul, matvec
from materials_gcts_stationary_production_signature import (
    PortGraphProduction, ProductionBoundary, ProductionChild,
    ProductionPort, PromotionObservation, canonicalize_production,
    compare_stationary_productions, stationary_evidence)

ROTATION = ((0.0, -1.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0))
HALF_TURN = ((-1.0, 0.0, 0.0),
             (0.0, -1.0, 0.0),
             (0.0, 0.0, 1.0))


def _production(scale=1.0, rotation=IDENTITY, shift=(0., 0., 0.),
                order=(0, 1, 2, 3), gauge_child=-1,
                chemistry=("Na", "Cl", "Na", "Yb")):
    base = ((0., 0., 0.), (1., 0., 0.), (0., 2., 0.),
            (.25, .5, 3.))
    world = tuple(tuple(shift[axis] + scale * matvec(rotation, point)[axis]
                        for axis in range(3)) for point in base)
    children = []
    for old in order:
        child_rotation = rotation
        if old == gauge_child:
            child_rotation = matmul(rotation, HALF_TURN)
        children.append(ProductionChild(
            (chemistry[old],), "right-handed", child_rotation, world[old],
            (IDENTITY, HALF_TURN)))
    old_to_new = {old: new for new, old in enumerate(order)}
    raw_ports = ((0, 1, ("face",), ("Na", "Cl")),
                 (1, 2, ("edge",), ("Cl", "Na")),
                 (2, 3, ("vertex",), ("Na", "Yb")),
                 (3, 0, ("return",), ("Yb", "Na")))
    ports = tuple(ProductionPort(
        old_to_new[source], old_to_new[target], key, overlap)
        for source, target, key, overlap in raw_ports)
    boundary = (ProductionBoundary(
        old_to_new[2], "outgoing", ("Cd",), ("outer-face",), ("Na",)),)
    return PortGraphProduction(tuple(children), ports, boundary)


def _observation(level, production):
    return PromotionObservation(level, production, 3, 0.0, 10, True)


def test_signature_quotients_only_admissible_similarity_gauges():
    lower = _production()
    upper = _production(
        2.0, ROTATION, (7., -3., 2.), (3, 1, 0, 2), gauge_child=2)
    left = canonicalize_production(lower)
    right = canonicalize_production(upper)
    comparison = compare_stationary_productions(lower, upper)
    assert left.normalized_key == right.normalized_key
    assert comparison.stationary
    assert math.isclose(comparison.learned_similarity_scale, 2.0)
    assert comparison.maximum_normalized_translation_residual < 1e-12
    assert comparison.maximum_rotation_residual < 1e-12


def test_chemistry_chirality_and_directed_port_incidence_are_preserved():
    base = _production()
    chemistry = _production(2.0, chemistry=("Na", "Cl", "Cd", "Yb"))
    assert not compare_stationary_productions(base, chemistry).stationary

    changed_child = list(_production(2.0).children)
    original = changed_child[0]
    changed_child[0] = ProductionChild(
        original.chemistry_key, "left-handed", original.rotation,
        original.translation, original.proper_symmetries)
    chiral = PortGraphProduction(
        tuple(changed_child), _production(2.0).internal_ports,
        _production(2.0).boundary_slots)
    assert not compare_stationary_productions(base, chiral).stationary

    target = _production(2.0)
    first = target.internal_ports[0]
    reversed_port = ProductionPort(
        first.target, first.source, first.port_key, first.overlap_chemistry)
    incidence = PortGraphProduction(
        target.children, (reversed_port,) + target.internal_ports[1:],
        target.boundary_slots)
    assert not compare_stationary_productions(base, incidence).stationary


def test_improper_mirror_and_nonuniform_dilation_do_not_compare_stationary():
    base = _production()
    target = _production(2.0)
    mirrored_children = tuple(ProductionChild(
        child.chemistry_key, child.chirality_key, child.rotation,
        (-child.translation[0], child.translation[1], child.translation[2]),
        child.proper_symmetries) for child in target.children)
    mirrored = PortGraphProduction(
        mirrored_children, target.internal_ports, target.boundary_slots)
    assert not compare_stationary_productions(base, mirrored).stationary

    stretched_children = list(target.children)
    child = stretched_children[-1]
    stretched_children[-1] = ProductionChild(
        child.chemistry_key, child.chirality_key, child.rotation,
        (child.translation[0], child.translation[1],
         child.translation[2] * 1.1), child.proper_symmetries)
    stretched = PortGraphProduction(
        tuple(stretched_children), target.internal_ports,
        target.boundary_slots)
    assert not compare_stationary_productions(base, stretched).stationary


def test_stationarity_needs_two_adjacent_scale_comparisons():
    one_scale = stationary_evidence((
        _observation(0, _production()),
        _observation(1, _production(2.0)),
    ))
    assert not one_scale.stationary

    evidence = stationary_evidence((
        _observation(0, _production()),
        _observation(1, _production(2.0)),
        _observation(2, _production(4.0)),
    ))
    assert evidence.stationary
    assert evidence.observed_levels == (0, 1, 2)
    assert math.isclose(evidence.learned_similarity_scale, 2.0)


def test_arbitrary_copied_patch_and_amorphous_levels_are_rejected():
    copied = PortGraphProduction(_production().children, (), ())
    copied_evidence = stationary_evidence((
        _observation(0, copied), _observation(1, copied),
        _observation(2, copied)))
    assert not copied_evidence.stationary

    amorphous_middle = _production(2.0)
    children = list(amorphous_middle.children)
    child = children[2]
    children[2] = ProductionChild(
        child.chemistry_key, child.chirality_key, child.rotation,
        (child.translation[0] + .137, child.translation[1] - .091,
         child.translation[2] + .043), child.proper_symmetries)
    amorphous_middle = PortGraphProduction(
        tuple(children), amorphous_middle.internal_ports,
        amorphous_middle.boundary_slots)
    amorphous = stationary_evidence((
        _observation(0, _production()),
        _observation(1, amorphous_middle),
        _observation(2, _production(4.0))))
    assert not amorphous.stationary


if __name__ == "__main__":
    test_signature_quotients_only_admissible_similarity_gauges()
    test_chemistry_chirality_and_directed_port_incidence_are_preserved()
    test_improper_mirror_and_nonuniform_dilation_do_not_compare_stationary()
    test_stationarity_needs_two_adjacent_scale_comparisons()
    test_arbitrary_copied_patch_and_amorphous_levels_are_rejected()
    print("normalized stationary production signature: all assertions passed")
