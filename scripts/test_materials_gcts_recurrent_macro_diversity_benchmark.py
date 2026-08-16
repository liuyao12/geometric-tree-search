#!/usr/bin/env python3
"""Regression for the train-only role-diverse frontier audit."""

from materials_gcts_recurrent_macro_diversity_benchmark import evaluate


def test_role_diverse_frontier_audit():
    result = evaluate(shuffle_trials=3, fit_steps=40)
    assert result.every_learned_parent_type_selected
    assert result.selected_frontiers >= result.learned_macro_types
    assert result.fit_parent_types == result.learned_macro_types
    assert result.calibration_patch_id not in result.fit_patch_ids
    assert result.calibration_parent_types > 0
    assert result.calibration_precision == 1. or \
        result.calibration_recall == 0.
    assert result.patch_specific_role_occurrences >= result.selected_frontiers
    assert result.raw_training_candidates > result.original_centered_candidates
    assert result.negative_training_records > 0
    assert result.parent_types_with_negative_actions > 1
    assert result.target_factory_calls == 1
    assert result.target_opened_after_all_executions
    assert result.first_wave_candidate_sets_identical
    assert not result.target_used_during_selection_fit_or_execution
    assert not result.marking_descriptor_uses_raw_ids_or_absolute_frame
    assert result.matched_work_target_atoms >= 0
    assert result.benchmark_passed == (
        result.precision_gate and result.causal_advantage_gate)


if __name__ == "__main__":
    test_role_diverse_frontier_audit()
    print("recurrent macro diversity benchmark: assertions passed")
