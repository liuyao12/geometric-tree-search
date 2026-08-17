#!/usr/bin/env python3

import json
from dataclasses import asdict

from materials_gcts_cdyb_site_resolved_completion_section import (
    aggregate_action_confidence, evaluate, score_site_confidence)


def test_site_resolved_section_is_train_only_and_nested():
    result = evaluate()
    assert result.train_windows == 5
    assert result.shifted_frontiers == 35
    assert result.frozen_macro_candidates == 28
    assert result.site_samples == 360
    assert result.supported_sites == 250
    assert result.unsupported_sites == 110
    assert result.exact_actions == 14
    assert result.mixed_or_wrong_actions == 14
    assert result.feature_count == 10
    assert result.grouped_outer_folds == 5
    assert result.null_trials == 31
    assert len(result.outer_aggregation_by_fold) == 5
    assert result.final_action_aggregation == "minimum"
    assert result.outer_site_auc > result.null_site_auc_best
    assert result.site_auc_empirical_p == 1 / 32
    # Site confidence transfers between train windows; the whole-action
    # aggregation is not significant against site-label nulls and remains red.
    assert result.action_auc_empirical_p == .5
    assert result.outer_site_threshold_by_fold == (1., 1., 1., .65, 1.)
    assert result.outer_site_accepted_by_fold == (0, 0, 0, 68, 0)
    assert result.outer_site_threshold_precision < .95
    assert result.final_site_acceptance_threshold == 1.
    assert result.final_threshold_oof_precision == 1.
    assert result.final_threshold_oof_recall == 0.
    assert result.final_threshold_oof_accepted == 0
    assert not result.nonempty_95_precision_threshold_found
    assert result.corpus_digest == (
        "8d17c6876984ab0c172779bfed25e11df6bf0adced8a490b7fbb6ea666dbc7c6")
    assert result.site_corpus_digest == result.corpus_digest
    assert result.frozen_section_digest == (
        "e51ea838175a4ab932f5c10188c1f47d68ed2a7951c52b1e9b49f5870e1c0073")
    assert result.model_manifest_digest == (
        "0c0993d5920b8901621fc9670bb63b9bac013fc3b275917ebd4f6e800e1c09f6")
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
