#!/usr/bin/env python3

from materials_gcts_recurrent_macro_marking_benchmark import evaluate


def test_recurrent_macro_marking_is_sealed_and_honestly_gated():
    result = evaluate()
    assert result.causal_training_traces > 0
    assert result.independent_training_components >= 5
    assert result.maximum_interaction_order == 2
    assert result.shuffle_trials == 31
    assert result.target_factory_calls == 1
    assert result.target_opened_after_all_traces_frozen
    assert result.candidate_ids_identical_first_wave
    assert result.stable_tie_fallback_identical
    assert (result.exact_context_candidates +
            result.empty_context_backoff_candidates +
            result.unseen_context_candidates ==
            result.evaluation_commit_candidates)
    assert result.unique_marking_scores_first_wave >= 1
    assert not result.target_used_during_fit_or_execution
    assert not result.nacl_null_control
    assert result.marked.matched_work.matched_correct_atoms > 0
    assert result.unmarked.matched_work.matched_correct_atoms > 0
    assert result.benchmark_passed == (
        result.precision_gate and result.causal_advantage_gate)
    assert result.exact_context_candidates == 0
    assert result.empty_context_backoff_candidates == 0
    assert result.unseen_context_candidates == result.evaluation_commit_candidates
    assert result.first_wave_rank_inversions == 0
    assert result.unique_marking_scores_first_wave == 1


if __name__ == "__main__":
    test_recurrent_macro_marking_is_sealed_and_honestly_gated()
    print("recurrent macro causal marking benchmark: assertions passed")
