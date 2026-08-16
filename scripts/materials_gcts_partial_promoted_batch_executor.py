#!/usr/bin/env python3
"""Target-free conflict-free batching of partial promoted completions."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class FrozenPartialBatchPolicy:
    minimum_score: float = 0.
    maximum_accepted: int = 64
    macro_scores: tuple[tuple[int, float], ...] = ()


@dataclass(frozen=True)
class PartialBatchDecision:
    candidate_id: str
    macro_id: int
    score: float
    emitted_sites: int
    decision: str


@dataclass(frozen=True)
class PartialPromotedBatchExecution:
    policy: FrozenPartialBatchPolicy
    input_candidates: int
    geometrically_eligible_candidates: int
    immutable_candidate_digest: str
    decisions: tuple[PartialBatchDecision, ...]
    accepted_candidate_ids: tuple[str, ...]
    accepted_macro_ids: tuple[int, ...]
    committed_sites: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    sites_after: tuple[tuple[Hashable, tuple[float, float, float]], ...]
    rejected_internal_conflict: int
    rejected_existing_collision: int
    rejected_outside_boundary: int
    rejected_duplicate_union: int
    rejected_threshold: int
    rejected_budget: int
    rejected_pair_conflict: int
    rejected_antichain_comparability: int
    every_commit_is_whole_child_union: bool
    accepted_set_pairwise_compatible: bool
    accepted_set_is_antichain: bool
    target_used: bool


def _site_key(site, tolerance):
    return (repr(site[0]),) + tuple(round(value / tolerance)
                                    for value in site[1])


def _normalize_sites(sites, tolerance):
    by_coordinate = {}
    positions = {}
    for species, raw_point in sites:
        point = tuple(float(value) for value in raw_point)
        if len(point) != 3 or not all(math.isfinite(value) for value in point):
            return None
        coordinate = tuple(round(value / tolerance) for value in point)
        prior = by_coordinate.get(coordinate)
        if prior is not None and prior != species:
            return None
        by_coordinate[coordinate] = species
        positions.setdefault(coordinate, point)
    return tuple((by_coordinate[key], positions[key])
                 for key in sorted(by_coordinate))


def _compatible(left, right, tolerance, exclusion):
    for left_species, left_point in left:
        for right_species, right_point in right:
            distance = math.dist(left_point, right_point)
            if distance <= tolerance:
                if left_species != right_species:
                    return False
            elif distance < exclusion:
                return False
    return True


def _internally_compatible(sites, tolerance, exclusion):
    for index, (_species, point) in enumerate(sites):
        for _other_species, other in sites[index + 1:]:
            distance = math.dist(point, other)
            if tolerance < distance < exclusion:
                return False
    return True


def _candidate_id(candidate, sites, tolerance):
    payload = (candidate.macro_id,
               getattr(candidate, "frozen_parent_type", None),
               tuple((child.node, child.type_id) for child in
                     candidate.missing_children),
               tuple(sorted(_site_key(site, tolerance) for site in sites)))
    return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


def execute_partial_promoted_batch(
        candidates: Sequence[object], *, minimum_distance: float,
        occupied_sites: Sequence[tuple[Hashable, Sequence[float]]] = (),
        public_boundary: object | None = None,
        policy: FrozenPartialBatchPolicy = FrozenPartialBatchPolicy(),
        pose_tolerance: float = .03,
) -> PartialPromotedBatchExecution:
    """Commit complete missing-child unions under a frozen local policy."""
    if (minimum_distance <= 0 or pose_tolerance <= 0 or
            not math.isfinite(minimum_distance) or
            not math.isfinite(pose_tolerance)):
        raise ValueError("distance tolerances must be finite and positive")
    if (not math.isfinite(policy.minimum_score) or
            policy.maximum_accepted < 1):
        raise ValueError("invalid frozen batch policy")
    scores = dict(policy.macro_scores)
    if (len(scores) != len(policy.macro_scores) or
            any(not math.isfinite(value) for value in scores.values())):
        raise ValueError("macro scores must be unique and finite")
    occupied = _normalize_sites(occupied_sites, pose_tolerance)
    if occupied is None:
        raise ValueError("occupied sites contain a colored conflict")
    exclusion = max(pose_tolerance, minimum_distance * .45)
    decisions = []
    eligible = {}
    geometry_candidate_ids = []
    internal = existing = outside = duplicate = 0
    for candidate in candidates:
        child_sites = tuple(tuple(site) for child in candidate.missing_children
                            for site in child.sites)
        union = _normalize_sites(child_sites, pose_tolerance)
        if (union is None or
                not _internally_compatible(union, pose_tolerance, exclusion)):
            internal += 1
            continue
        candidate_id = _candidate_id(candidate, union, pose_tolerance)
        score = scores.get(candidate.macro_id, 0.)
        if public_boundary is not None and any(
                math.dist(point, public_boundary.origin) >
                public_boundary.outer_radius + pose_tolerance
                for _species, point in union):
            outside += 1
            decisions.append(PartialBatchDecision(
                candidate_id, candidate.macro_id, score, len(union),
                "outside-public-boundary"))
            continue
        if not _compatible(union, occupied, pose_tolerance, exclusion):
            existing += 1
            decisions.append(PartialBatchDecision(
                candidate_id, candidate.macro_id, score, len(union),
                "existing-site-collision"))
            continue
        geometry_candidate_ids.append(candidate_id)
        union_key = tuple(sorted(_site_key(site, pose_tolerance)
                                 for site in union))
        rank = (-score, candidate.macro_id, candidate_id)
        prior = eligible.get(union_key)
        if prior is None or rank < prior[0]:
            if prior is not None:
                duplicate += 1
            eligible[union_key] = (rank, candidate_id, candidate, union, score)
        else:
            duplicate += 1

    # This digest is deliberately frozen before score, threshold, budget,
    # deduplication-winner, and greedy compatibility decisions.
    frozen_ids = tuple(sorted(geometry_candidate_ids))
    digest = hashlib.sha256(repr(frozen_ids).encode("utf-8")).hexdigest()
    accepted = []
    threshold = budget = pair = antichain = 0
    for _rank, candidate_id, candidate, union, score in sorted(
            eligible.values(), key=lambda item: item[0]):
        keys = frozenset(_site_key(site, pose_tolerance) for site in union)
        if score < policy.minimum_score:
            threshold += 1
            decisions.append(PartialBatchDecision(
                candidate_id, candidate.macro_id, score, len(union),
                "below-frozen-threshold"))
            continue
        if len(accepted) >= policy.maximum_accepted:
            budget += 1
            decisions.append(PartialBatchDecision(
                candidate_id, candidate.macro_id, score, len(union),
                "deferred-by-frozen-budget"))
            continue
        if any(keys < prior[4] or prior[4] < keys for prior in accepted):
            antichain += 1
            decisions.append(PartialBatchDecision(
                candidate_id, candidate.macro_id, score, len(union),
                "comparable-emission-set"))
            continue
        if any(not _compatible(union, prior[3], pose_tolerance, exclusion)
               for prior in accepted):
            pair += 1
            decisions.append(PartialBatchDecision(
                candidate_id, candidate.macro_id, score, len(union),
                "pairwise-collision"))
            continue
        accepted.append((_rank, candidate_id, candidate, union, keys, score))
        decisions.append(PartialBatchDecision(
            candidate_id, candidate.macro_id, score, len(union), "commit"))

    committed = _normalize_sites(tuple(
        site for item in accepted for site in item[3]), pose_tolerance) or ()
    after = _normalize_sites(tuple(occupied) + tuple(committed),
                             pose_tolerance) or ()
    accepted_keys = tuple(item[4] for item in accepted)
    pairwise = all(_compatible(left[3], right[3], pose_tolerance, exclusion)
                   for index, left in enumerate(accepted)
                   for right in accepted[index + 1:])
    is_antichain = all(not (left < right or right < left)
                       for index, left in enumerate(accepted_keys)
                       for right in accepted_keys[index + 1:])
    return PartialPromotedBatchExecution(
        policy, len(candidates), len(eligible), digest,
        tuple(sorted(decisions, key=lambda item: item.candidate_id)),
        tuple(item[1] for item in accepted),
        tuple(item[2].macro_id for item in accepted), committed, after,
        internal, existing, outside, duplicate, threshold, budget, pair,
        antichain,
        len(committed) == len({_site_key(site, pose_tolerance)
                               for item in accepted for site in item[3]}),
        pairwise, is_antichain, False)
