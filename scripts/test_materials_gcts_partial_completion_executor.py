#!/usr/bin/env python3
"""Synthetic two-level control for target-blind partial macro execution."""

from types import SimpleNamespace

from materials_gcts_oriented_overlap_ports import (
    ClusterOccurrence, IDENTITY, OrientedOverlapPort, PortAtlas,
    canonical_relative_pose, make_prototype)
from materials_gcts_partial_completion_executor import (
    PartialCompletionLevel, execute_partial_completion_hierarchy,
    execute_partial_completion_level)
from materials_gcts_port_graph_macros import BoundarySlot, MacroChildPlacement


def _render(prototype, shift):
    return tuple((species, tuple(point[index] + shift[index]
                                 for index in range(3)))
                 for species, point in prototype.sites)


def _union(*groups):
    result = {}
    for species, point in (site for group in groups for site in group):
        result.setdefault(tuple(round(value, 8) for value in point),
                          (species, point))
    return tuple(result[key] for key in sorted(result))


def _port(parent, child, translation, observations=8):
    _rotation, _translation, key = canonical_relative_pose(
        parent, child, IDENTITY, translation, 1e-6)
    port = OrientedOverlapPort(
        parent.type_id, child.type_id, IDENTITY, translation,
        (), (), key, observations)
    return port, key


def _fixture():
    first = make_prototype(0, (
        ("A", (0., 0., 0.)), ("B", (.4, 0., 0.)),
        ("C", (0., .6, 0.))))
    second = make_prototype(1, (
        ("D", (0., 0., 0.)), ("E", (.4, 0., 0.)),
        ("F", (0., .6, 0.))))
    port01, key01 = _port(first, second, (2., 0., 0.))
    lower = SimpleNamespace(
        prototypes=(first, second),
        atlas=PortAtlas((port01,), 0, 0, 0, 0, 0, ()),
        boundary_ports=(), minimum_distance=.4)
    macro1 = SimpleNamespace(
        macro_id=7,
        child_placements=(
            MacroChildPlacement(0, 0, IDENTITY, (0., 0., 0.)),
            MacroChildPlacement(1, 1, IDENTITY, (2., 0., 0.)),
            MacroChildPlacement(2, 0, IDENTITY, (4., 0., 0.))),
        edges=(), boundary_slots=(
            BoundarySlot(0, "outgoing", 1, (0, 1, key01), 8, 1.),))
    parent1 = make_prototype(10, _union(
        _render(first, (0., 0., 0.)), _render(second, (2., 0., 0.)),
        _render(first, (4., 0., 0.))))
    promoted1 = SimpleNamespace(prototypes=(parent1,))

    port11, key11 = _port(parent1, parent1, (4., 0., 0.))
    lower2 = SimpleNamespace(
        prototypes=(parent1,),
        atlas=PortAtlas((port11,), 0, 0, 0, 0, 0, ()),
        boundary_ports=(), minimum_distance=.4)
    macro2 = SimpleNamespace(
        macro_id=9,
        child_placements=(
            MacroChildPlacement(0, 10, IDENTITY, (0., 0., 0.)),
            MacroChildPlacement(1, 10, IDENTITY, (4., 0., 0.))),
        edges=(), boundary_slots=(
            BoundarySlot(0, "outgoing", 10, (10, 10, key11), 6, 1.),))
    parent2 = make_prototype(20, _union(
        _render(parent1, (0., 0., 0.)),
        _render(parent1, (4., 0., 0.))))
    promoted2 = SimpleNamespace(prototypes=(parent2,))
    return first, (
        PartialCompletionLevel(lower, (macro1,), ((7, 10),), promoted1),
        PartialCompletionLevel(lower2, (macro2,), ((9, 20),), promoted2))


def test_two_level_whole_macro_batches_self_feed_without_target():
    seed_prototype, levels = _fixture()
    seed = (ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),)
    result = execute_partial_completion_hierarchy(
        levels, seed, explicit_seed_sites=seed_prototype.sites,
        maximum_waves_per_level=1, maximum_accepted_per_wave=1,
        pose_tolerance=1e-6)
    assert len(result.levels) == 2
    assert all(item.whole_macro_actions == 1 for item in result.levels)
    assert result.levels[0].primitive_child_actions == 2
    assert result.levels[1].primitive_child_actions == 1
    assert all(item.promoted_occurrences for item in result.levels)
    assert all(item.candidate_digests_frozen_before_scorer
               for item in result.levels)
    assert all(item.certificates and all(
        certificate.exact_frozen_rhs_geometry and certificate.proper_se3 and
        certificate.frozen_port_witnessed and
        certificate.emitted_is_exact_difference and
        certificate.collision_free and certificate.promoted_pose_exact
        for certificate in item.certificates) for item in result.levels)
    assert not result.target_api_present and not result.target_used


def test_same_level_second_wave_uses_committed_children():
    seed_prototype, levels = _fixture()
    seed = (ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),)
    result = execute_partial_completion_level(
        levels[0], seed, explicit_seed_sites=seed_prototype.sites,
        maximum_waves=2, maximum_accepted_per_wave=1,
        pose_tolerance=1e-6)
    assert len(result.waves) == 2
    assert result.waves[0].accepted_whole_macros == 1
    assert result.waves[1].accepted_whole_macros == 1
    assert result.waves[1].candidate_count > 0
    assert result.self_fed
    assert len(set(item.candidate_digest for item in result.waves)) == 2


if __name__ == "__main__":
    test_two_level_whole_macro_batches_self_feed_without_target()
    test_same_level_second_wave_uses_committed_children()
    print("partial completion multiwave executor: passed")
