#!/usr/bin/env python3
"""Regression for the sealed local H2O orientation-marking experiment."""

from materials_gcts_ice_orientation_marking_benchmark import evaluate


def test_local_geometry_does_not_overclaim_proton_branch_selection() -> None:
    result = evaluate()
    assert result.source_atoms == 3840
    assert result.frozen_ports == 8
    assert result.train_patches == 5 and result.heldout_patches == 3
    assert result.minimum_patch_center_separation > result.required_patch_separation
    assert result.raw_train_heldout_molecule_overlap == 0
    assert result.training_domains == 70
    assert result.training_alternatives == 291
    assert result.training_positive_alternatives == 66
    assert result.heldout_candidate_domains == 65
    assert result.heldout_target_matched_domains == 51
    assert result.heldout_alternatives == 191
    assert result.heldout_exact_supply_domains == 40
    assert result.candidate_digest == \
        "c9f23613b2b8a595495a470e024076d25b6e9ddea485c014099728fdcaa2c2f1"
    assert result.model_digest == \
        "fafb81a25297a3ebd1cb0f0a49bab790ecf40d7cc88cec008728b2d2b8533416"
    assert result.learned.exact_anchor_domains == 51
    assert result.learned.exact_selected == 9
    assert result.learned.wrong_selected == 56
    assert result.learned.recall == .225
    assert result.unmarked.exact_selected == 8
    assert result.shuffled_exact_median == 9
    assert result.shuffled_exact_best == 9
    assert result.empirical_p == .75
    assert result.learned_beats_unmarked
    assert not result.learned_beats_shuffles
    assert not result.orientation_marking_gate_passed
    assert result.candidates_frozen_before_target
    assert result.target_open_count == 3
    assert not result.target_used_for_fit_or_ranking
    assert result.proper_motion_invariant_features
    assert not result.canonical_branch_materialized_during_growth


if __name__ == "__main__":
    test_local_geometry_does_not_overclaim_proton_branch_selection()
    print("ice orientation marking benchmark: honest red")
