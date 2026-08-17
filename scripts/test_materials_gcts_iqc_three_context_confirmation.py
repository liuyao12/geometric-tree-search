#!/usr/bin/env python3

from materials_gcts_iqc_three_context_confirmation import evaluate


def test_ordinal_channel_context_fails_on_tenth_nucleus():
    report = evaluate()
    result = report.result
    assert report.all_target_balls_pairwise_disjoint
    assert report.model_frozen_before_confirmation
    assert report.contexts == (0, 4, 12)
    assert report.independent_after_twelve_observations == 3
    assert report.context_after_twelve_values[5] == .8
    assert result.executed_waves == 3
    assert result.wave_candidate_true_sites[0][10] == 1
    assert result.wave_selected_paths == ((4, 5, 12),
                                          (6, 5, 11),
                                          (4, 4, 11))
    assert result.wave_true_sites == (0, 0, 0)
    assert result.wave_false_sites == (1, 1, 1)
    assert not result.all_executed_actions_exact
    assert not result.target_used_for_selection
    assert not report.three_wave_spatial_confirmation_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_ordinal_channel_context_fails_on_tenth_nucleus()
    print("IQC three-context confirmation tests: passed")
