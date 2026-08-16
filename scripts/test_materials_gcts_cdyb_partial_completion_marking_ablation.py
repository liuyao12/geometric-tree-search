#!/usr/bin/env python3

from materials_gcts_cdyb_partial_completion_marking_ablation import evaluate


def test_cdyb_partial_completion_marking_ablation_is_sealed():
    result = evaluate()
    assert result.training_frontiers == 5
    assert result.training_candidates == 14
    assert sum(result.training_candidates_by_frontier) == 14
    assert result.training_positive_actions == 8
    assert sum(result.training_positives_by_frontier) == 8
    assert result.training_negative_actions == 6
    assert result.lopo_threshold == .25
    assert result.lopo_top_budget == 5
    assert result.lopo_selected_actions == 14
    assert result.lopo_exact_actions == 8
    assert result.eval_candidates == 82
    assert result.eval_exact_candidates_posthoc == 6
    assert result.eval_candidate_precision_posthoc == 6 / 82
    assert result.eval_candidate_digest == \
        "641e87611f7182f5631ca92e538e01e3e4f176d5df0f6a9f93ef3c641178e345"
    assert result.identical_candidate_ids_all_arms
    assert result.shuffle_trials == 31
    assert result.marked.selected_actions == 5
    assert result.marked.exact_actions == 1
    assert result.marked.action_precision == .2
    assert result.marked.action_recall_among_exact_candidates == 1 / 6
    assert result.marked.correct_novel_sites == 16
    assert result.marked.wrong_novel_sites == 18
    assert result.marked.site_precision == 16 / 34
    assert result.constant.correct_novel_sites == 13
    assert result.frequency.correct_novel_sites == 8
    assert result.marked_empirical_p == 1.
    assert not result.marking_gate_passed
    assert result.train_eval_raw_id_intersection == 0
    assert result.domains_disjoint
    assert result.target_opened_after_all_eval_rankings_frozen
    assert not result.target_used_for_candidate_enumeration_or_ranking
    assert result.descriptor_only_no_family_cell_origin_or_target_features


if __name__ == "__main__":
    test_cdyb_partial_completion_marking_ablation_is_sealed()
    print("CdYb partial completion marking ablation: passed")
