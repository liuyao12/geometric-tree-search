#!/usr/bin/env python3
"""Slow exact-geometry claim audit for max-nodes-five IQC transfer."""

from materials_gcts_iqc_max5_transfer_claim_audit import evaluate


def test_four_level_transfer_is_not_mislabeled_exponential():
    result = evaluate()
    assert result.raw_domains_mutually_disjoint
    assert result.train_heldout_raw_ids_disjoint
    assert result.raw_types_by_level == (520, 53, 16, 3)
    assert result.selected_types_by_level == (148, 10, 4, 1)
    assert result.exact_heldout_types_by_level == (148, 10, 4, 1)
    assert len(result.child_arity_histograms_by_level) == 4
    assert all(sum(count for _, count in histogram) == types
               for histogram, types in zip(
                   result.child_arity_histograms_by_level,
                   result.selected_types_by_level))
    assert len(result.exact_raw_support_size_histograms_by_level) == 4
    assert all(result.exact_complete_representation_by_level)
    assert result.raw_atom_coverage_by_level == (
        1220 / 1248, 1033 / 1248, 925 / 1248, 870 / 1248)
    assert result.residual_atom_terminals_by_level == (28, 215, 323, 378)
    assert result.minimum_distinct_namespaces_by_level == (2, 3, 3, 3)
    assert result.minimum_atom_disjoint_occurrences_by_level == (2, 3, 3, 3)
    assert result.exact_four_level_heldout_reencoding
    assert not result.autonomous_growth_or_emission
    assert not result.heldout_used_for_selection
    assert not result.family_phi_cell_radius_used

    # Exact transfer depth is not a stationary production or an exponential
    # certificate.  Any finite one-step support increase is reported but is
    # insufficient without three repeated >3 transitions and strict semantics.
    assert not result.strict_stationary
    assert result.common_normalized_production_keys_by_adjacent_levels == (
        0, 0, 0)
    assert result.common_normalized_production_keys_by_three_levels == (0, 0)
    assert result.strict_adapted_records == 0
    assert sum(count for _, count in result.strict_rejection_reason_histogram
               ) == result.strict_adaptation_rejections
    assert result.scale_population_eligible_three_level_witnesses == 0
    assert result.maximum_raw_support_atoms_by_level == (78, 78, 110, 111)
    assert not result.any_represented_support_amplification_over_three
    assert not result.three_consecutive_amplifications_over_three
    assert not result.exponential_claim


if __name__ == "__main__":
    test_four_level_transfer_is_not_mislabeled_exponential()
    print("max5 IQC transfer claim audit: all assertions passed")
