#!/usr/bin/env python3

from materials_gcts_iqc_contextual_value_confirmation import evaluate


def test_carried_context_selects_two_exact_self_fed_waves():
    report = evaluate()
    result = report.result
    assert report.all_target_balls_pairwise_disjoint
    assert report.model_frozen_before_confirmation
    assert report.model.contexts == (0, 4)
    assert report.model.maximum_context_order == 1
    assert report.context_zero_values[3] == 5 / 6
    assert report.context_after_four_values[5] == 3 / 4
    assert report.context_after_four_values[11] == 3 / 4
    assert result.executed_waves == 2
    assert result.wave_selected_paths == ((4, 12, 11), (12, 9, 10))
    assert result.wave_true_sites == (1, 1)
    assert result.wave_false_sites == (0, 0)
    assert result.correct_sites == result.emitted_sites == 2
    assert result.all_executed_actions_exact
    assert not result.target_used_for_selection
    assert report.two_wave_spatial_confirmation_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_carried_context_selects_two_exact_self_fed_waves()
    print("IQC contextual-value confirmation tests: passed")
