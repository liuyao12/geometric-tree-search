#!/usr/bin/env python3
"""Focused matched-frontier policy adapter controls."""

from materials_gcts_cdyb_continuous_completion_marking import (
    FEATURE_NAMES, FrozenContinuousCompletionMarking, _features)
from materials_gcts_partial_completion_execution_policy import (
    FrozenMacroFrequencyPolicy, adapt_continuous_completion_marking,
    completion_continuous_features)
from materials_gcts_partial_completion_policy_arms import (
    FrozenCompletionPolicyArm, execute_identical_completion_policy_arms,
    SingleUsePostPlanTargetFactory, freeze_completion_execution_plan)
from materials_gcts_partial_completion_executor import _dynamic_program
from materials_gcts_oriented_overlap_ports import ClusterOccurrence, IDENTITY
from test_materials_gcts_partial_completion_executor import _fixture


def _model(weights):
    return FrozenContinuousCompletionMarking(
        FEATURE_NAMES, (0.,) * len(FEATURE_NAMES),
        (1.,) * len(FEATURE_NAMES), tuple(weights), 0., .1, False, False)


def test_continuous_adapter_matches_committed_feature_definition():
    seed_prototype, levels = _fixture()
    level = levels[0]
    seed = (ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),)
    # Obtain the immutable candidate/completion pair through the public frontier.
    from materials_gcts_partial_promoted_frontier import (
        enumerate_partial_promoted_completions)
    dynamic = _dynamic_program(level.frozen_lower_program, seed, 1e-6)
    frontier = enumerate_partial_promoted_completions(
        dynamic, level.alternatives,
        minimum_matched_children=1, explicit_seed_sites=seed_prototype.sites,
        frozen_parent_types=level.alternative_parent_types,
        pose_tolerance=1e-6)
    from materials_gcts_partial_completion_marking import (
        freeze_completion_candidate)
    completion = frontier.completions[0]
    macro = level.alternatives[0]
    macro.atom_union = level.promoted_program.prototypes[0].sites
    candidate = freeze_completion_candidate(
        dynamic, macro, completion,
        pose_tolerance=1e-6)
    actual = completion_continuous_features(
        candidate, completion, macro, level.frozen_lower_program.minimum_distance)
    expected = _features(
        candidate, completion, macro, level.frozen_lower_program.minimum_distance)
    assert actual == expected


def test_continuous_constant_frequency_and_shuffle_share_frozen_batch():
    seed_prototype, levels = _fixture()
    levels[0].alternatives[0].atom_union = \
        levels[0].promoted_program.prototypes[0].sites
    seed = (ClusterOccurrence(0, 0, IDENTITY, (0., 0., 0.)),)
    weights = [0.] * len(FEATURE_NAMES)
    weights[0] = 1.
    continuous = adapt_continuous_completion_marking(_model(weights))
    shuffled_weights = tuple(reversed(weights))
    shuffled = adapt_continuous_completion_marking(_model(shuffled_weights))
    frequency = FrozenMacroFrequencyPolicy(((7, .8),), .5, 10, False)
    result = execute_identical_completion_policy_arms(
        levels[0], seed, explicit_seed_sites=seed_prototype.sites,
        arms=(
            FrozenCompletionPolicyArm("continuous", continuous),
            FrozenCompletionPolicyArm("constant", None),
            FrozenCompletionPolicyArm("frequency", frequency),
            FrozenCompletionPolicyArm("shuffle-0", shuffled)),
        maximum_accepted=1, pose_tolerance=1e-6)
    assert result.identical_frozen_candidate_batches
    assert result.candidate_count > 0 and len(result.candidate_digest) == 64
    assert all(item.execution.waves[0].candidate_digest ==
               result.candidate_digest for item in result.arms)
    assert all(item.execution.candidate_digests_frozen_before_scorer
               for item in result.arms)
    assert not result.target_api_present and not result.target_used
    plan = freeze_completion_execution_plan(
        result, source_digest="51090f27da810177f3b68c1cb3ebd90b4b17efe4",
        training_corpus_digest="a" * 64,
        arm_model_digests=tuple((item.name, f"{index + 1:064x}")
                                for index, item in enumerate(result.arms)))
    assert plan.candidate_ids == result.candidate_ids
    assert len(plan.plan_digest) == 64
    assert all(rule[2:] == (1, 1) for rule in plan.decision_rules)
    assert plan.executor_target_free and plan.target_factory_open_after_plan_only
    assert plan.target_factory_single_use_required
    calls = []
    opener = SingleUsePostPlanTargetFactory(
        lambda: calls.append("opened") or ("scorer-only",))
    assert opener.open(plan) == ("scorer-only",)
    assert calls == ["opened"]
    try:
        opener.open(plan)
    except RuntimeError:
        pass
    else:
        raise AssertionError("target factory opened more than once")


def test_target_tainted_continuous_model_fails_closed():
    model = FrozenContinuousCompletionMarking(
        FEATURE_NAMES, (0.,) * len(FEATURE_NAMES),
        (1.,) * len(FEATURE_NAMES), (0.,) * len(FEATURE_NAMES),
        0., .1, True, False)
    try:
        adapt_continuous_completion_marking(model)
    except ValueError:
        pass
    else:
        raise AssertionError("target-tainted model was admitted")


if __name__ == "__main__":
    test_continuous_adapter_matches_committed_feature_definition()
    test_continuous_constant_frequency_and_shuffle_share_frozen_batch()
    test_target_tainted_continuous_model_fails_closed()
    print("partial completion policy arms: passed")
