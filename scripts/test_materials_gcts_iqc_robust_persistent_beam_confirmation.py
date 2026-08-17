#!/usr/bin/env python3

from materials_gcts_iqc_robust_persistent_beam_confirmation import evaluate


def test_fifth_nucleus_keeps_exact_option_but_value_selects_false_branch():
    report = evaluate()
    result = report.result
    assert report.all_target_balls_pairwise_disjoint
    assert report.policy_frozen_before_confirmation
    assert result.robust_leave_one_nucleus_out_marking
    assert result.lookahead_depth == 3
    assert result.beam_width == result.branching_width == 4
    assert result.evaluated_branches == 36
    assert result.first_candidate_true_sites == (0, 0, 0, 1)
    assert result.first_candidate_false_sites == (1, 1, 1, 0)
    assert result.selected_path_ranks == (2, 3, 2)
    assert result.correct_sites == 0
    assert result.false_sites == 1
    assert not result.target_used_for_selection
    assert not report.spatial_confirmation_passed
    assert not report.stationary_or_exponential_certificate


if __name__ == "__main__":
    test_fifth_nucleus_keeps_exact_option_but_value_selects_false_branch()
    print("robust persistent IQC beam confirmation tests: passed")
