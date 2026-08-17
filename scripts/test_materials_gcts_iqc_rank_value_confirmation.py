#!/usr/bin/env python3

from materials_gcts_iqc_rank_value_confirmation import evaluate


def test_learned_value_recovers_exact_action_on_sixth_nucleus():
    report = evaluate()
    result = report.result
    assert report.all_target_balls_pairwise_disjoint
    assert report.model_frozen_before_confirmation
    assert report.model.positive_counts == (0, 0, 1, 2)
    assert report.model.posterior_values == (.25, .25, .5, .75)
    assert result.first_candidate_true_sites == (0, 0, 0, 1)
    assert result.first_candidate_false_sites == (1, 1, 1, 0)
    assert result.first_candidate_value_scores == (.25, .25, .5, .75)
    assert result.selected_path_ranks == (4, 2, 2)
    assert result.correct_sites == result.emitted_sites == 1
    assert result.false_sites == 0
    assert not result.target_used_for_selection
    assert report.spatial_confirmation_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_learned_value_recovers_exact_action_on_sixth_nucleus()
    print("IQC rank-value confirmation tests: passed")
