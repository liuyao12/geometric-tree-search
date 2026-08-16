#!/usr/bin/env python3
"""Synthetic contracts for conflict-free promoted batching."""

from types import SimpleNamespace

from materials_gcts_partial_promoted_batch_executor import (
    FrozenPartialBatchPolicy, execute_partial_promoted_batch)


def _candidate(macro_id, groups, parent=None):
    children = tuple(SimpleNamespace(
        node=index, type_id=index,
        sites=tuple((species, tuple(point)) for species, point in sites))
                     for index, sites in enumerate(groups))
    return SimpleNamespace(macro_id=macro_id, frozen_parent_type=parent,
                           missing_children=children)


def test_whole_union_collision_rejects_every_child():
    candidate = _candidate(1, ((("A", (2., 0., 0.)),),
                               (("B", (0., 0., 0.)),)))
    result = execute_partial_promoted_batch(
        (candidate,), minimum_distance=1.,
        occupied_sites=(("X", (0., 0., 0.)),))
    assert not result.accepted_candidate_ids
    assert result.rejected_existing_collision == 1
    assert result.committed_sites == ()
    internal = _candidate(2, ((("A", (2., 0., 0.)),),
                              (("B", (2.1, 0., 0.)),)))
    rejected = execute_partial_promoted_batch(
        (internal,), minimum_distance=1.)
    assert rejected.rejected_internal_conflict == 1
    assert not rejected.accepted_candidate_ids


def test_ranked_batch_is_pairwise_compatible_antichain_and_deterministic():
    left = _candidate(1, ((("A", (2., 0., 0.)),
                           ("B", (3., 0., 0.))),))
    right = _candidate(2, ((("A", (2., 0., 0.)),
                            ("C", (4., 0., 0.))),))
    conflict = _candidate(3, ((("X", (3., 0., 0.)),),))
    subset = _candidate(4, ((("A", (2., 0., 0.)),),))
    policy = FrozenPartialBatchPolicy(
        macro_scores=((1, 4.), (2, 3.), (3, 2.), (4, 1.)))
    first = execute_partial_promoted_batch(
        (left, right, conflict, subset), minimum_distance=1., policy=policy)
    permuted = execute_partial_promoted_batch(
        (subset, conflict, right, left), minimum_distance=1., policy=policy)
    different_policy = execute_partial_promoted_batch(
        (left, right, conflict, subset), minimum_distance=1.,
        policy=FrozenPartialBatchPolicy(
            minimum_score=9., maximum_accepted=1))
    assert first.immutable_candidate_digest == permuted.immutable_candidate_digest
    assert first.immutable_candidate_digest == \
        different_policy.immutable_candidate_digest
    assert first.accepted_candidate_ids == permuted.accepted_candidate_ids
    assert first.accepted_macro_ids == (1, 2)
    assert first.rejected_pair_conflict == 1
    assert first.rejected_antichain_comparability == 1
    assert first.accepted_set_pairwise_compatible
    assert first.accepted_set_is_antichain
    assert first.every_commit_is_whole_child_union
    assert not first.target_used


def test_frozen_threshold_budget_boundary_and_union_dedupe():
    first = _candidate(1, ((("A", (2., 0., 0.)),),))
    duplicate = _candidate(2, ((("A", (2., 0., 0.)),),))
    second = _candidate(3, ((("B", (4., 0., 0.)),),))
    outside = _candidate(4, ((("C", (9., 0., 0.)),),))
    policy = FrozenPartialBatchPolicy(
        minimum_score=1., maximum_accepted=1,
        macro_scores=((1, 3.), (2, 2.), (3, 1.), (4, 4.)))
    result = execute_partial_promoted_batch(
        (first, duplicate, second, outside), minimum_distance=1.,
        public_boundary=SimpleNamespace(
            origin=(0., 0., 0.), outer_radius=5.), policy=policy)
    assert result.accepted_macro_ids == (1,)
    assert result.rejected_duplicate_union == 1
    assert result.rejected_outside_boundary == 1
    assert result.rejected_budget == 1


if __name__ == "__main__":
    test_whole_union_collision_rejects_every_child()
    test_ranked_batch_is_pairwise_compatible_antichain_and_deterministic()
    test_frozen_threshold_budget_boundary_and_union_dedupe()
    print("partial promoted batch executor: all assertions passed")
