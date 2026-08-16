#!/usr/bin/env python3

from materials_gcts_recurrent_macro_geometry_marking_benchmark import evaluate


def test_id_free_geometry_marking_is_sealed_and_honestly_gated():
    result = evaluate()
    assert result.training_patches == 5
    assert result.positive_training_candidates > 0
    assert result.negative_training_candidates > 0
    assert result.specifications_compared == 9
    assert result.selected_train_only
    assert result.shuffle_trials == 31
    assert result.target_factory_calls == 1
    assert result.target_opened_after_all_executions
    assert result.first_wave_candidate_sets_identical
    assert (result.exact_context_candidates +
            result.pose_backoff_candidates +
            result.chemistry_backoff_candidates +
            result.kind_backoff_candidates + result.unseen_candidates ==
            result.evaluation_candidates)
    assert not result.target_used_during_fit_or_execution
    assert not result.descriptor_uses_raw_type_or_production_ids
    assert not result.descriptor_uses_absolute_coordinates_family_cell_or_target
    assert result.marked.matched_work.matched_correct_atoms > 0
    assert result.benchmark_passed == (
        result.precision_gate and result.causal_advantage_gate)


if __name__ == "__main__":
    test_id_free_geometry_marking_is_sealed_and_honestly_gated()
    print("recurrent macro geometry marking benchmark: assertions passed")
