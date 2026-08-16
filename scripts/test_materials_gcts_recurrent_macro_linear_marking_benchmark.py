#!/usr/bin/env python3

from materials_gcts_recurrent_macro_linear_marking_benchmark import evaluate


def test_linear_geometry_marking_is_sealed_and_honestly_gated():
    result = evaluate()
    assert result.training_patches == 5
    assert result.positive_training_candidates > 0
    assert result.negative_training_candidates > 0
    assert result.feature_dimensions >= 24
    assert result.selected_ridge in result.ridge_values_compared
    assert result.selected_train_only
    assert result.validation_beats_global
    assert result.leave_one_patch_out_threshold_precision >= .99
    assert result.leave_one_patch_out_threshold_recall >= .25
    assert result.shuffle_trials == 31
    assert result.target_factory_calls == 1
    assert result.target_opened_after_all_executions
    assert result.first_wave_candidate_sets_identical
    assert result.first_wave_unique_scores > 1
    assert result.first_wave_rank_inversions > 0
    assert not result.target_used_during_fit_or_execution
    assert not result.descriptor_uses_raw_type_production_action_ids
    assert not result.descriptor_uses_absolute_coordinates_family_cell_or_target
    assert result.matched_work_comparable == (
        result.matched_work_target_atoms > 0)
    if not result.matched_work_comparable:
        assert result.empirical_p_value == 1.
    assert result.benchmark_passed == (
        result.precision_gate and result.causal_advantage_gate)


if __name__ == "__main__":
    test_linear_geometry_marking_is_sealed_and_honestly_gated()
    print("recurrent macro linear marking benchmark: assertions passed")
