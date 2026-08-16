#!/usr/bin/env python3
"""Matched-frontier target-free policy arms for partial completions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Sequence

from materials_gcts_partial_completion_execution_policy import (
    CompletionExecutionPolicy)
from materials_gcts_partial_completion_executor import (
    PartialCompletionExecution, PartialCompletionLevel,
    execute_partial_completion_level)


@dataclass(frozen=True)
class FrozenCompletionPolicyArm:
    name: str
    policy: CompletionExecutionPolicy
    minimum_score: float | None = None


@dataclass(frozen=True)
class FrozenCompletionPolicyArmResult:
    name: str
    minimum_score: float | None
    execution: PartialCompletionExecution


@dataclass(frozen=True)
class FrozenCompletionPolicyComparison:
    candidate_digest: str
    candidate_count: int
    candidate_ids: tuple[str, ...]
    arms: tuple[FrozenCompletionPolicyArmResult, ...]
    identical_frozen_candidate_batches: bool
    matched_acceptance_cap: int
    target_api_present: bool
    target_used: bool


@dataclass(frozen=True)
class FrozenCompletionExecutionPlan:
    schema_version: int
    source_digest: str
    training_corpus_digest: str
    arm_model_digests: tuple[tuple[str, str], ...]
    candidate_digest: str
    candidate_ids: tuple[str, ...]
    decision_rules: tuple[tuple[str, float | None, int, int], ...]
    selected_candidate_ids: tuple[tuple[str, tuple[str, ...]], ...]
    executor_target_free: bool
    target_factory_open_after_plan_only: bool
    target_factory_single_use_required: bool
    plan_digest: str


def _hex_digest(value, lengths=(64,)):
    return (isinstance(value, str) and len(value) in lengths and
            all(character in "0123456789abcdef" for character in value))


def _execution_plan_digest(plan):
    payload = asdict(plan)
    payload.pop("plan_digest")
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode()).hexdigest()


class SingleUsePostPlanTargetFactory:
    """Mechanically order one opaque target opening after a valid frozen plan."""

    def __init__(self, factory):
        self._factory = factory
        self._opened = False

    def open(self, plan: FrozenCompletionExecutionPlan):
        if self._opened:
            raise RuntimeError("target factory is single-use")
        if (not isinstance(plan, FrozenCompletionExecutionPlan) or
                not plan.executor_target_free or
                _execution_plan_digest(plan) != plan.plan_digest):
            raise ValueError("target cannot open before a valid frozen plan")
        # Mark consumed before invoking external code, including if it fails.
        self._opened = True
        return self._factory()


def freeze_completion_execution_plan(
    comparison: FrozenCompletionPolicyComparison, *, source_digest: str,
    training_corpus_digest: str, arm_model_digests,
) -> FrozenCompletionExecutionPlan:
    """Serialize decisions before a single-use scorer/target is constructed."""
    model_digests = tuple(sorted(arm_model_digests))
    names = tuple(item.name for item in comparison.arms)
    if (not _hex_digest(source_digest, (40, 64)) or
            not _hex_digest(training_corpus_digest) or
            set(name for name, _digest in model_digests) != set(names) or
            any(not _hex_digest(digest) for _name, digest in model_digests)):
        raise ValueError("execution plan needs frozen source/corpus/model digests")
    rules = tuple((item.name, item.minimum_score,
                   comparison.matched_acceptance_cap, 1)
                  for item in comparison.arms)
    selected = tuple((item.name, tuple(
        certificate.candidate_id for certificate in
        item.execution.certificates)) for item in comparison.arms)
    provisional = FrozenCompletionExecutionPlan(
        1, source_digest, training_corpus_digest, model_digests,
        comparison.candidate_digest, comparison.candidate_ids, rules,
        selected, True, True, True, "")
    digest = _execution_plan_digest(provisional)
    return replace(provisional, plan_digest=digest)


def execute_identical_completion_policy_arms(
    level: PartialCompletionLevel, seed_occurrences, *,
    arms: Sequence[FrozenCompletionPolicyArm], explicit_seed_sites=(),
    public_boundary=None, maximum_accepted: int = 32,
    minimum_child_coverage: float = 0., pose_tolerance: float = .03,
    level_index: int = 1,
) -> FrozenCompletionPolicyComparison:
    """Execute one identical frozen frontier under several immutable policies.

    A single wave is deliberate: after different commits, later frontiers are
    causally different and must not be described as identical candidate batches.
    """
    arms = tuple(arms)
    if not arms or len({item.name for item in arms}) != len(arms):
        raise ValueError("policy arms need unique nonempty names")
    results = []
    for arm in arms:
        execution = execute_partial_completion_level(
            level, seed_occurrences, explicit_seed_sites=explicit_seed_sites,
            public_boundary=public_boundary, marking=arm.policy,
            maximum_waves=1, maximum_accepted_per_wave=maximum_accepted,
            minimum_marking_score=arm.minimum_score,
            minimum_child_coverage=minimum_child_coverage,
            pose_tolerance=pose_tolerance, level_index=level_index)
        results.append(FrozenCompletionPolicyArmResult(
            arm.name, arm.minimum_score, execution))
    signatures = {(item.execution.waves[0].candidate_count,
                   item.execution.waves[0].candidate_digest,
                   item.execution.waves[0].candidate_ids)
                  for item in results}
    if len(signatures) != 1:
        raise AssertionError("ranking policy changed the frozen candidate batch")
    count, digest, candidate_ids = next(iter(signatures))
    if any(item.execution.target_api_present or item.execution.target_used
           for item in results):
        raise AssertionError("policy comparison crossed a target boundary")
    return FrozenCompletionPolicyComparison(
        digest, count, candidate_ids, tuple(results), True,
        maximum_accepted, False, False)
