#!/usr/bin/env python3
"""Fast contract tests for depth-independent lineage continuation."""

from types import SimpleNamespace

from materials_gcts_lineage_continuation import (
    FrozenLineageContinuationFailure, attempt_frozen_lineage,
    extend_frozen_lineage)


def test_lineage_continuation_is_target_blind_and_depth_independent():
    calls = []

    def runtime_loader():
        return {"frozen": True}

    def replay(source, runtime, block, radius):
        calls.append(("replay", tuple(block), radius))
        return SimpleNamespace(
            actions=tuple(block),
            positions=tuple(source.seed_positions) + tuple(
                point for point, _color in block),
            species=tuple(source.seed_species) + tuple(
                color for _point, color in block)), 6

    def tree(source, runtime, radius, telemetry, use_geometry_cache):
        calls.append(("tree", len(source.seed_positions), radius,
                      use_geometry_cache))
        telemetry.update({
            "naive_geometry_expansions": 12,
            "unique_geometry_expansions": 7,
            "saved_geometry_expansions": 5,
            "geometry_cache_hits": 5})
        return (SimpleNamespace(actions=(
            ((4., 0., 0.), "X"), ((4., 1., 0.), "Y"),
            ((4., 0., 1.), "Z"))),), (3, 7, 1)

    actions = tuple(((float(block), float(index), 0.), "XYZ"[index])
                    for block in (1, 2, 3) for index in range(3))
    result = extend_frozen_lineage(
        lineage_id=("case", 4), center=(0., 0., 0.),
        seed_positions=((0., 0., 0.),), seed_species=("X",),
        prior_actions=actions, replay_radii=(10., 20., 30.),
        next_radius=40., runtime_loader=runtime_loader,
        replay=replay, tree=tree)
    assert result.prior_blocks == 3
    assert result.valid_orders_per_block == (6, 6, 6)
    assert result.candidate_counts_by_depth == (3, 7, 1)
    assert len(result.successors) == 1
    assert len(result.successors[0].all_actions) == 12
    assert result.unique_geometry_expansions == 7
    assert result.saved_geometry_expansions == 5
    assert not result.target_used
    assert [row[0] for row in calls] == ["replay"] * 3 + ["tree"]

    def rejecting_replay(source, runtime, block, radius):
        raise AssertionError("frozen block has no unique colored replay")

    rejected = attempt_frozen_lineage(
        lineage_id=("rejected", 1), center=(0., 0., 0.),
        seed_positions=((0., 0., 0.),), seed_species=("X",),
        prior_actions=actions, replay_radii=(10., 20., 30.),
        next_radius=40., runtime_loader=runtime_loader,
        replay=rejecting_replay, tree=tree)
    assert isinstance(rejected, FrozenLineageContinuationFailure)
    assert rejected.failure_kind == "AssertionError"
    assert "unique colored replay" in rejected.failure_message
    assert not rejected.target_used
    try:
        extend_frozen_lineage(
            lineage_id=0, center=(0., 0., 0.),
            seed_positions=((0., 0., 0.),), seed_species=("X",),
            prior_actions=actions, replay_radii=(10., 20., 30.),
            next_radius=30., runtime_loader=runtime_loader,
            replay=replay, tree=tree)
    except ValueError:
        pass
    else:
        raise AssertionError("non-increasing continuation radius accepted")


if __name__ == "__main__":
    test_lineage_continuation_is_target_blind_and_depth_independent()
    print("depth-independent lineage continuation test passed")
