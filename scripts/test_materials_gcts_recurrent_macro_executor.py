#!/usr/bin/env python3
"""Focused safety tests for target-blind recurrent macro execution."""

from dataclasses import replace

from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_recurrent_macro_executor import (
    GEOMETRY_LINEAR_FEATURE_NAMES, ExecutionBoundary, FrozenExecutionPolicy,
    FrozenLinearGeometryScorer, execute_recurrent_macro_program,
    geometry_candidate_features, geometry_candidate_mark,
    score_recurrent_macro_execution)
from test_materials_gcts_port_graph_macros import _synthetic_program


def _level():
    atomic = _synthetic_program()
    macros = mine_port_graph_macros(
        atomic, maximum_nodes=3, geometry_tolerance=1e-6)
    return promote_macro_types(
        atomic, macros.macro_types, pose_tolerance=1e-6,
        minimum_shared_atoms=1)


def test_executor_self_feeds_frozen_ports_before_posthoc_scoring():
    level = _level()
    result = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=2,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.))
    assert result.accepted
    assert len(result.waves) == 2
    assert result.waves[1].frontier_nodes == result.waves[0].accepted_placements
    assert result.self_fed and result.exact_certificates
    assert result.longest_parent_child_depth == 1
    assert result.reachable_fixed_point and not result.stopped_by_wave_limit
    assert not result.target_used_for_proposals_or_ranking
    assert all(item.decision in {
        "accepted", "duplicate-pose", "outside-public-boundary",
        "colored-or-exclusion-collision", "insufficient-required-overlap",
        "interior-duplicate", "duplicate-rendered-union", "wave-cap",
        "commit-conflict", "below-frozen-consensus"} for item in result.trace)
    score = score_recurrent_macro_execution(
        result, tuple(site[0] for site in result.sites),
        tuple(site[1] for site in result.sites), tolerance=1e-6)
    assert score.precision == 1.0
    assert not score.target_used_for_proposals_or_ranking
    evidence = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=1,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        policy=FrozenExecutionPolicy("evidence-first"))
    consensus = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=1,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        policy=FrozenExecutionPolicy("consensus", .5))
    causal = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=1,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        policy=FrozenExecutionPolicy(
            strategy="causal-marking", maximum_incoming_context=2,
            marking_scores=(((0, 0, ()), 1.),)))
    candidate = result.eligible_candidates[0]
    moved_candidate = replace(
        candidate, candidate_id="unrelated-action-id", parent_node=999,
        emitted_site_keys=tuple(
            (key[0], key[1] + 1000, key[2] - 2000, key[3] + 3000)
            for key in candidate.emitted_site_keys))
    geometry_descriptor = geometry_candidate_mark(
        result, candidate, include_incoming=False)
    geometry = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=1,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        policy=FrozenExecutionPolicy(
            strategy="geometry-marking", maximum_incoming_context=2,
            geometry_marking_scores=((geometry_descriptor, 9.),)))
    geometry_marked = next(
        item for item in geometry.eligible_candidates
        if item.candidate_id == candidate.candidate_id)
    assert geometry_marked.marking_score == 9.
    assert geometry_candidate_mark(
        result, moved_candidate, include_incoming=False) == geometry_descriptor
    features = geometry_candidate_features(level, result, candidate)
    assert features == candidate.geometry_features
    assert geometry_candidate_features(level, result, moved_candidate) == features
    weights = tuple(1. if name == "live_overlap_fraction" else 0.
                    for name in GEOMETRY_LINEAR_FEATURE_NAMES)
    linear_model = FrozenLinearGeometryScorer(
        GEOMETRY_LINEAR_FEATURE_NAMES,
        (0.,) * len(GEOMETRY_LINEAR_FEATURE_NAMES),
        (1.,) * len(GEOMETRY_LINEAR_FEATURE_NAMES), weights, .25)
    linear = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=1,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        policy=FrozenExecutionPolicy(
            strategy="geometry-linear", maximum_incoming_context=2,
            geometry_linear_scorer=linear_model))
    linear_marked = next(
        item for item in linear.eligible_candidates
        if item.candidate_id == candidate.candidate_id)
    overlap_index = GEOMETRY_LINEAR_FEATURE_NAMES.index(
        "live_overlap_fraction")
    assert linear_marked.marking_score == .25 + features[overlap_index]
    assert linear_marked.geometry_features == features
    pruned_linear = execute_recurrent_macro_program(
        level, level.occurrences[:1], maximum_waves=1,
        maximum_accepted_per_wave=8, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        policy=FrozenExecutionPolicy(
            strategy="geometry-linear", maximum_incoming_context=2,
            geometry_linear_scorer=linear_model,
            geometry_linear_minimum_score=100.))
    assert not pruned_linear.accepted
    assert any(item.decision == "below-frozen-linear-mark"
               for item in pruned_linear.trace)
    assert (result.waves[0].candidate_digest ==
            evidence.waves[0].candidate_digest ==
            consensus.waves[0].candidate_digest ==
            causal.waves[0].candidate_digest ==
            geometry.waves[0].candidate_digest ==
            linear.waves[0].candidate_digest ==
            pruned_linear.waves[0].candidate_digest)


def test_public_boundary_and_subminimum_collision_fail_closed():
    level = _level()
    seed = level.occurrences[:1]
    center = seed[0].translation
    bounded = execute_recurrent_macro_program(
        level, seed, maximum_waves=1, pose_tolerance=1e-6,
        boundary=ExecutionBoundary(center, .01))
    assert not bounded.accepted
    assert bounded.rejected_outside_boundary > 0
    assert bounded.exhausted
    assert bounded.reachable_fixed_point

    baseline = execute_recurrent_macro_program(
        level, seed, maximum_waves=1, pose_tolerance=1e-6,
        boundary=ExecutionBoundary((0., 0., 0.), 100.))
    emitted = next(site for site in baseline.sites
                   if site not in baseline.seed_sites)
    blocked_level = replace(level, minimum_distance=1.)
    blocker = (("blocker", (emitted[1][0], emitted[1][1] + .2,
                            emitted[1][2])),)
    blocked = execute_recurrent_macro_program(
        blocked_level, seed, explicit_seed_sites=blocker,
        maximum_waves=1, pose_tolerance=.01,
        boundary=ExecutionBoundary((0., 0., 0.), 100.))
    assert blocked.rejected_colored_collisions > 0
    assert len(blocked.accepted) < len(baseline.accepted)


if __name__ == "__main__":
    test_executor_self_feeds_frozen_ports_before_posthoc_scoring()
    test_public_boundary_and_subminimum_collision_fail_closed()
    print("target-blind recurrent macro executor: passed")
