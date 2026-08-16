#!/usr/bin/env python3
"""Adversarial stationary-claim and optional-vocabulary regression."""

from materials_gcts_iqc_exponential_claim_boundary import (
    adversarial_contract_self_test, audit_missing_level_one_types,
    audit_pipeline_adversaries)


def test_every_stationary_claim_guard_has_an_independent_red_control():
    assert all(adversarial_contract_self_test())


def test_three_missing_types_are_not_promoted_to_optional_grammar():
    result = audit_missing_level_one_types()
    assert result.train_atoms == 2048
    assert result.heldout_atoms == 1248
    assert result.raw_patch_domains_mutually_disjoint
    assert result.train_heldout_raw_ids_disjoint
    assert result.frozen_level_one_types == 259
    assert result.replayed_level_one_types == 256
    assert tuple(item.macro_id for item in result.missing) == (184, 185, 252)
    assert tuple(item.training_occurrences for item in result.missing) == (
        2, 2, 2)
    assert all(item.training_patches == (2,) for item in result.missing)
    assert all(item.atoms_unique_against_other_types == 0
               for item in result.missing)
    assert result.heldout_atom_cover_with_missing_absent == 1.
    assert result.safe_optional_for_observed_atom_cover
    assert not result.statistical_rarity_established
    assert result.heldout_zero_of_three_patch_presence_upper_95 > .6
    assert result.next_level_macros_using_missing_types == 2
    assert result.transferred_exact_promoted_levels == 0
    assert not result.current_stationary_claim
    assert not result.safe_optional_for_recursive_grammar


def test_real_iqc_geometry_and_semantic_negative_controls():
    result = audit_pipeline_adversaries()
    assert result.iqc_input_permutation_invariant
    assert result.iqc_generic_proper_se3_invariant
    assert result.shuffled_semantic_control_rejected
    assert result.perturbed_semantic_control_rejected
    assert result.amorphous_macro_and_stationarity_rejected
    assert result.family_phi_cell_expected_radius_unused
    assert result.passed


if __name__ == "__main__":
    test_every_stationary_claim_guard_has_an_independent_red_control()
    test_three_missing_types_are_not_promoted_to_optional_grammar()
    test_real_iqc_geometry_and_semantic_negative_controls()
    print("IQC exponential claim boundary: all assertions passed")
