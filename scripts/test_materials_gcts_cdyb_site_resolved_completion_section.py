#!/usr/bin/env python3

import json
from dataclasses import asdict

from materials_gcts_cdyb_site_resolved_completion_section import (
    aggregate_action_confidence, evaluate, score_site_confidence)


def test_site_resolved_section_is_train_only_and_nested():
    result = evaluate()
    assert result.train_windows == 5
    assert result.shifted_frontiers == 105
    assert result.seed_radii == (.4 * 14., .5 * 14., .6 * 14.)
    assert result.frozen_macro_candidates == 123
    assert result.site_samples == 1245
    assert result.supported_sites == 871
    assert result.unsupported_sites == 374
    assert result.exact_actions == 77
    assert result.mixed_or_wrong_actions == 46
    assert result.feature_count == 10
    assert result.grouped_outer_folds == 5
    assert result.null_trials == 31
    assert len(result.outer_aggregation_by_fold) == 5
    assert result.final_action_aggregation == "lower-quartile"
    assert result.outer_site_auc > result.null_site_auc_best
    assert result.site_auc_empirical_p == 1 / 32
    assert result.action_auc_empirical_p == 1 / 32
    # The final candidate is nonempty and zero-error on five-window OOF data,
    # but selection of its safety margin is not itself fully nested.
    assert result.selected_zero_error_logit_margin == 1.5
    assert result.fixed_margin_outer_precision > .97
    assert result.fixed_margin_minimum_nonempty_fold_precision > .96
    assert result.fixed_margin_nonempty_folds == 4
    assert result.outer_site_accepted_by_fold == (4, 4, 60, 162, 60)
    assert result.outer_site_threshold_precision < .95
    assert result.fully_nested_margin_selection_precision < .95
    assert not result.fully_nested_margin_selection_passed
    assert result.final_site_acceptance_threshold == 0.9990244124431729
    assert result.final_threshold_oof_precision == 1.
    assert result.final_threshold_oof_recall == 0.08036739380022963
    assert result.final_threshold_oof_accepted == 70
    assert result.nonempty_95_precision_threshold_found
    assert result.corpus_digest == (
        "8f41d3ab65018c397d1ae1f9dbb75608837d59f076baeb88defe062b284a65a4")
    assert result.site_corpus_digest == result.corpus_digest
    assert result.frozen_section_digest == (
        "d220c705dc39a1b21ed983d57e5d302202f344c8af9dd1902d60936a31e491b4")
    assert result.model_manifest_digest == (
        "0b392873a21889f62f37f1435eb272d076c81dc62ae94bab60a31bcda814acea")
    assert json.loads(result.serialized_frozen_section) == json.loads(
        json.dumps(asdict(result.frozen_section)))
    assert not result.frozen_section.target_used
    assert not result.frozen_section.candidate_id_or_global_coordinate_feature_used
    assert result.all_fit_and_selection_data_from_five_training_windows
    assert not result.confirmatory_or_prior_eval_nucleus_used
    assert not result.candidate_geometry_or_ids_changed
    site_score = score_site_confidence(
        result.frozen_section, result.frozen_section.means)
    assert 0. < site_score < 1.
    assert aggregate_action_confidence(
        result.frozen_section, (site_score, site_score / 2)) == site_score / 2


if __name__ == "__main__":
    test_site_resolved_section_is_train_only_and_nested()
    print("CdYb site-resolved completion section: passed")
