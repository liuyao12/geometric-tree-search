#!/usr/bin/env python3

from materials_gcts_iqc_recurrent_branch_value_audit import evaluate


def test_expanded_recurrent_branch_value_is_green_development_only():
    report = evaluate()
    assert report.development_groups == 30
    assert report.development_examples == 354
    assert report.positive_examples == 211
    assert report.groups_with_exact_path == 21
    assert report.baseline_selected_exact_groups == 17
    assert report.selected_neighbors == 9
    assert report.recurrent_selected_exact_groups == 20
    assert report.recurrent_selection_precision >= .95
    assert report.candidate_digest_matches
    assert report.model_digest_matches
    assert report.confirmation_cumulative_rank == 10
    assert report.confirmation_recurrent_rank == 1
    assert report.confirmation_selected_exact
    assert not report.branch_features_use_coordinates_or_ids
    assert not report.target_used_for_candidate_generation
    assert not report.target_used_for_capacity_selection
    assert report.consumed_confirmation_used_only_after_fit
    assert not report.fresh_confirmation_claimed
    assert report.development_gate_passed


if __name__ == "__main__":
    test_expanded_recurrent_branch_value_is_green_development_only()
    print("IQC recurrent branch value audit passed")
