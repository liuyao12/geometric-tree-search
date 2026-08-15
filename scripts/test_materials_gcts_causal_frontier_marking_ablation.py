#!/usr/bin/env python3
"""Contract tests for sealed causal incoming-port marking ablation."""

from __future__ import annotations

from materials_gcts_causal_frontier_marking_ablation import (
    CausalGrowthTrace, FrozenFrontierAction,
    run_causal_marking_ablation)


def main() -> None:
    traces = []
    candidates = []
    correct = {}
    parent_type = 7
    contexts = tuple((100 + index,) for index in range(12))
    actions = tuple(1000 + index for index in range(len(contexts)))
    for context_index, context in enumerate(contexts):
        right_action = actions[context_index]
        wrong_action = actions[(context_index + 1) % len(actions)]
        for repeat in range(24):
            traces.append(CausalGrowthTrace(
                repeat * len(contexts) + context_index, parent_type,
                context, right_action,
                (repeat * len(contexts) + context_index,)))
        correct_site = ("X", context_index, 0, 0)
        wrong_site = ("X", context_index, 1, 0)
        wrong_id = len(candidates)
        right_id = wrong_id + 1
        # The target-blind baseline intentionally sees the wrong alternative
        # first; marking must recover the causal context/action association.
        candidates.extend((
            FrozenFrontierAction(
                wrong_id, context_index, parent_type, context,
                wrong_action, (wrong_site,), (0, context_index)),
            FrozenFrontierAction(
                right_id, context_index, parent_type, context,
                right_action, (correct_site,), (1, context_index))))
        correct[wrong_id] = frozenset()
        correct[right_id] = frozenset((correct_site,))
    candidates = tuple(candidates)

    scorer_calls = []
    def sealed_scorer(frozen):
        scorer_calls.append(tuple(item.candidate_id for item in frozen))
        return {item.candidate_id: correct[item.candidate_id]
                for item in frozen}

    result = run_causal_marking_ablation(
        tuple(traces), candidates, sealed_scorer)
    assert len(scorer_calls) == 1
    assert scorer_calls[0] == tuple(item.candidate_id for item in candidates)
    assert result.maximum_interaction_order == 2
    assert result.shuffled_runs == 31 and len(result.shuffled) == 31
    assert result.matched_correct_novel_atoms == len(contexts)
    assert result.marked.proposal_checks == len(contexts)
    assert result.marked.geometric_backtracks == 0
    assert result.unmarked.geometric_backtracks == len(contexts)
    assert result.candidate_set_identical
    assert result.all_traces_causal_and_train_only
    assert result.within_parent_shuffle
    assert not result.heldout_labels_used_during_fit_or_candidate_freeze
    assert result.empirical_work_p_value <= .05
    assert result.benchmark_passed

    try:
        run_causal_marking_ablation(
            (CausalGrowthTrace(0, 0, (1, 2, 3), 4, (0,)),),
            candidates, sealed_scorer)
    except ValueError as error:
        assert "order <=2" in str(error)
    else:
        raise AssertionError("third-order context was not rejected")
    print("sealed causal frontier marking contract: all assertions passed")


if __name__ == "__main__":
    main()
