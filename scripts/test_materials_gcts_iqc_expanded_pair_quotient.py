#!/usr/bin/env python3
"""Regression for the expanded IQC pair-interaction quotient."""

from materials_gcts_iqc_expanded_pair_quotient import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.additive_baseline_correct_actions == 30
    assert report.additive_baseline_exact_groups == 14
    assert report.selected_correct_actions == 30
    assert report.selected_false_actions == 6
    assert report.exact_groups == 14
    assert report.selected_correct_by_group == (
        2, 0, 2, 2, 2, 2, 2, 2, 2, 0, 1, 2, 2, 2, 1, 2, 2, 2)
    assert min(report.audits[0].supported_pairs_by_fold) > 20_000
    assert not report.exact_candidate_geometry_changed
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("expanded IQC pair-quotient regression passed")


if __name__ == "__main__":
    main()
