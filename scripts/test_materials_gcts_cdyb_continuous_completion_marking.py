#!/usr/bin/env python3

from materials_gcts_cdyb_continuous_completion_marking import evaluate


def test_continuous_completion_marking_is_train_only_and_grouped():
    result = evaluate()
    assert result.train_windows == 5
    assert result.grouped_outer_folds == 5
    assert result.feature_count == 10
    assert result.base_candidates == 14
    assert result.base_positive == 8
    assert result.base_negative == 6
    assert result.base_negative_roles == 2
    assert result.expanded_frontiers_considered == 35
    assert result.expanded_candidates == 28
    assert result.expanded_positive == 14
    assert result.expanded_negative == 14
    assert result.expanded_negative_roles == 3
    assert result.expanded_corpus_admitted
    assert result.admitted_candidates == 28
    assert result.admitted_positive == 14
    assert result.admitted_negative == 14
    assert result.outer_lopo_logloss == 0.4403645527515108
    assert result.outer_lopo_auc == 0.8367346938775511
    assert result.outer_lopo_unique_scores == 10
    assert result.shift_admission_uses_all_five_labels
    assert result.lopo_diagnostic_not_fully_nested
    assert result.nested_outer_expansion_admitted_by_fold == (
        True, True, True, False, True)
    assert result.nested_outer_lopo_logloss == 0.5007810586193014
    assert result.nested_outer_lopo_auc == 0.8571428571428571
    assert result.nested_outer_lopo_unique_scores == 9
    assert result.training_corpus_digest == \
        "d4ddc8ae825f0e8919a2fd107633b32931dceca44bade4b6f6e2370fec675542"
    assert result.frozen_model_digest == \
        "da3aef6b32bbf69ce4013d846e1535a1d90521db446404c10c5dd3fcedf67dbe"
    assert result.selected_final_lambda == 1.
    assert result.frozen_model.feature_names == result.feature_names
    assert not result.frozen_model.target_used
    assert not result.frozen_model.id_family_cell_origin_features_used
    assert result.all_samples_from_five_training_windows
    assert not result.confirmatory_nucleus_opened_or_scored
    assert not result.target_used_outside_training_windows
    assert not result.raw_ids_family_cell_origin_or_prescribed_scale_used
    assert result.ready_for_future_frozen_confirmatory_test


if __name__ == "__main__":
    test_continuous_completion_marking_is_train_only_and_grouped()
    print("CdYb continuous completion marking: passed")
