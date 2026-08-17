#!/usr/bin/env python3

from materials_gcts_iqc_channel_count_confirmation import evaluate


def test_learned_twelve_channel_reach_passes_fresh_eighth_nucleus():
    report = evaluate()
    result = report.result
    assert report.aborted_seventh_result_unavailable
    assert report.all_target_balls_pairwise_disjoint
    assert report.policy_frozen_before_confirmation
    assert report.exact_training_ranks == (3, 4, 6, 7, 12)
    assert report.learned_channel_reach == 12
    assert report.retained_configuration_width == 4
    assert report.model.positive_counts == (0, 0, 1, 3, 0, 1, 1,
                                            0, 0, 0, 0, 1)
    assert result.branching_width == 12
    assert result.beam_width == 4
    assert result.evaluated_branches == 108
    assert result.selected_path_ranks == (4, 12, 11)
    assert result.correct_sites == result.emitted_sites == 1
    assert result.false_sites == 0
    assert result.all_executed_actions_exact
    assert not result.target_used_for_selection
    assert report.spatial_confirmation_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_learned_twelve_channel_reach_passes_fresh_eighth_nucleus()
    print("IQC learned-channel confirmation tests: passed")
