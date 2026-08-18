#!/usr/bin/env python3
"""Regression for nested compatible two-action IQC tree search."""

from materials_gcts_iqc_joint_action_pair_search import evaluate


def main():
    report = evaluate()
    assert report.total_groups == 18
    assert report.shortlist_size == 16
    assert report.selected_correct_actions == 30
    assert report.selected_false_actions == 6
    assert report.exact_groups == 14
    assert report.additive_baseline_correct_actions == 30
    assert report.selected_correct_by_group == (
        2, 0, 2, 2, 2, 2, 2, 2, 2, 0, 1, 2, 2, 2, 1, 2, 2, 2)
    assert set(report.heldout_pair_candidates_by_group) == {120}
    assert min(report.heldout_exact_pairs_by_group) > 0
    assert report.order_independent_antichain_search
    assert not report.exact_candidate_geometry_changed
    assert not report.next_confirmation_seed_or_target_accessed
    assert not report.development_gate_passed
    print("joint two-action IQC search regression passed")


if __name__ == "__main__":
    main()
