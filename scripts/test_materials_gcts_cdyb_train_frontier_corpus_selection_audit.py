#!/usr/bin/env python3
"""Contracts for the five-window Cd--Yb frontier corpus audit."""

from materials_gcts_cdyb_train_frontier_corpus_selection_audit import evaluate


def test_training_frontier_corpus_is_diverse_but_not_transfer_ready():
    result = evaluate()
    assert result.training_windows == 5 and result.training_atoms == 2385
    assert result.raw_candidates == 14
    assert result.raw_positive_candidates == 8
    assert result.raw_negative_candidates == 6
    assert result.selected_candidates == 7
    assert result.selected_positive_candidates == 4
    assert result.selected_negative_candidates == 3
    assert result.selected_mixed_failures == 3
    assert result.selected_unsupported_failures == 0
    assert result.unique_parent_roles == 5
    assert result.unique_port_roles == 6
    assert result.unique_joint_roles == 6
    assert result.joint_roles_shared_across_patches == 1
    assert result.selected_candidates_in_shared_joint_roles == 2
    assert result.maximum_patches_per_joint_role == 2
    assert result.label_mixed_exact_descriptor_roles == 0
    assert result.raw_role_effective_sample_size < result.raw_candidates
    assert result.selected_role_effective_sample_size < result.selected_candidates
    assert sum(value == 0 for value in
               result.lopo_exact_descriptor_coverage_by_patch) == 3
    assert not result.every_patch_has_selected_positive_and_negative
    assert result.every_validation_group_sealed
    assert not result.spatial_jitter_or_absolute_origin_used_for_selection
    assert not result.heldout_or_new_evaluation_nucleus_opened
    assert result.target_used_only_within_authorized_training_windows


if __name__ == "__main__":
    test_training_frontier_corpus_is_diverse_but_not_transfer_ready()
    print("CdYb training frontier corpus selection audit passed")
