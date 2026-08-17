#!/usr/bin/env python3

from materials_gcts_iqc_rank_value_multistep_diagnostic import evaluate


def test_valid_second_wave_channels_are_outside_active_width_four():
    report = evaluate()
    result = report.result
    assert result.wave_true_sites == (1, 0)
    assert result.wave_false_sites == (0, 1)
    assert result.exact_first_action_recovered
    assert not result.all_executed_actions_exact
    assert report.second_wave_first_exact_rank == 6
    assert report.second_wave_exact_ranks == (6, 12)
    assert not report.candidate_geometry_missing
    assert not report.sustained_exact_growth
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_valid_second_wave_channels_are_outside_active_width_four()
    print("IQC rank-value multistep diagnostic tests: passed")
