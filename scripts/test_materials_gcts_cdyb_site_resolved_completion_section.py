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
    # The searched logit-margin diagnostic remains red when its own selection
    # is nested.  A separate deterministic refit rule is evaluated below.
    assert result.selected_zero_error_logit_margin == 1.5
    assert result.fixed_margin_outer_precision > .97
    assert result.fixed_margin_minimum_nonempty_fold_precision > .96
    assert result.fixed_margin_nonempty_folds == 4
    assert result.outer_site_accepted_by_fold == (4, 4, 60, 162, 60)
    assert result.outer_site_threshold_precision < .95
    assert result.fully_nested_margin_selection_precision < .95
    assert not result.fully_nested_margin_selection_passed
    assert result.final_site_acceptance_threshold == 0.9898148321930725
    assert result.final_threshold_oof_precision == 0.981042654028436
    assert result.final_threshold_oof_recall == 0.23765786452353616
    assert result.final_threshold_oof_accepted == 211
    assert result.nonempty_95_precision_threshold_found
    assert result.group_refit_outer_correct == 207
    assert result.group_refit_outer_accepted == 211
    assert result.group_refit_outer_precision == 0.981042654028436
    assert result.group_refit_outer_recall == 0.23765786452353616
    assert result.group_refit_outer_precision_by_fold == (
        1., 1., 1., 0.9591836734693877, 1.)
    assert result.group_refit_outer_accepted_by_fold == (8, 29, 38, 98, 38)
    assert result.group_refit_minimum_nonempty_fold_precision > .95
    assert result.group_refit_nonempty_folds == 5
    assert result.group_refit_null_correct_best == 21
    assert result.group_refit_correct_empirical_p == 1 / 32
    assert result.group_refit_selector_passed
    assert result.group_refit_rule_exploratory_not_confirmatory
    assert not result.future_confirmatory_target_opened
    assert result.corpus_digest == (
        "932dcacb88c56c93572fd4302c0e3690c414553a2bf10d7f8badc21388d6c2b9")
    assert result.site_corpus_digest == result.corpus_digest
    assert result.frozen_section_digest == (
        "3add513d517b7c7f86e010c932398315938017936b678e8c986ccd45c5e4b596")
    assert result.model_manifest_digest == (
        "c8594c63d6b5bb38a33a275b5134fb04cef2cab1a578a67ab77563df0a596672")
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
