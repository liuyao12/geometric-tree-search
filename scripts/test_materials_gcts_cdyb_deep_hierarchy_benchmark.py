#!/usr/bin/env python3
"""Regression for the published Cd--Yb deep generic hierarchy."""

from materials_gcts_cdyb_deep_hierarchy_benchmark import evaluate


def test_cdyb_deep_hierarchy():
    result = evaluate()
    assert result.train_windows == 5
    assert result.train_atoms == 2385
    assert result.raw_domains_pairwise_disjoint
    assert result.complete_cover_with_gap_clusters
    assert result.repeated_covered_atoms == 2360
    assert result.gap_atoms == 25
    assert result.primitive_support_types == 274
    assert result.primitive_occurrences == 1697
    assert result.primitive_oriented_ports == 21056
    assert result.every_support_occurrence_window_local
    assert result.every_promoted_occurrence_window_local
    assert result.distinct_window_configuration_classes == 5
    assert result.admitted_types_by_level == (
        181, 76, 47, 32, 16, 12, 8, 4, 2, 0)
    assert result.quotient_types_by_level == (
        80, 36, 22, 15, 8, 6, 4, 2, 1, 0)
    assert result.independently_witnessed_quotient_types_by_level == (
        79, 36, 22, 15, 8, 6, 4, 2, 1, 0)
    assert result.single_window_quotient_types_by_level == (
        1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert result.artifact_occurrences_by_level == (
        1697, 162, 72, 44, 30, 16, 12, 8, 4, 2)
    assert result.maximum_atom_support_by_level == (
        67, 120, 201, 232, 307, 364, 420, 471, 472, 0)
    assert result.positive_hierarchy_levels == 9
    assert result.converged_at_evidence_exhaustion
    assert result.strict_stationary_audit_invoked
    assert result.stationary_witnesses == 0
    assert not result.stationary_or_exponential_claimed
    assert not result.target_family_cell_potential_source_sites_or_expected_scale_used
    assert result.hierarchy_gate_passed


if __name__ == "__main__":
    test_cdyb_deep_hierarchy()
    print("CdYb deep hierarchy benchmark passed")
