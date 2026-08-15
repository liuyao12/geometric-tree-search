#!/usr/bin/env python3
"""Slow regression for exact action-submacro recursive promotion."""

from materials_gcts_iqc_recursive_action_submacro_benchmark import evaluate


def test_six_patch_submacros_reach_two_positive_recursive_levels():
    result = evaluate()
    assert result.corpus_digest == (
        "8645b480d2e1caa1a620d3541df8b37a06213b27707e085bdb0d62bd70d8dfe8")
    assert result.initial_admitted_submacro_types == 11
    assert (result.promoted_prototypes,
            result.promoted_dense_occurrences) == (11, 22)
    assert result.namespaced_support_atoms == 311
    assert (result.promoted_overlap_ports,
            result.promoted_overlap_relations) == (36, 90)
    assert (result.promoted_boundary_ports,
            result.promoted_boundary_relations) == (26, 52)
    assert result.base_dense_occurrence_multiplicity_histogram == ((2, 11),)
    assert (result.sparse_source_nodes, result.sparse_source_edges) == (22, 36)
    assert (result.sparse_retained_nodes,
            result.sparse_retained_edges) == (16, 10)
    assert result.next_level_candidates == 38
    # Geometry is intentionally delayed until a graph class has enough
    # independent evidence; singleton graph classes are no longer counted as
    # exact geometry classes.
    assert result.next_level_exact_classes == 8
    assert result.next_level_admitted_types == 8
    assert result.next_level_quotient_types == 4
    assert result.next_level_exact_quotient_classes == (
        (0, 2), (1, 5), (3, 6), (4, 7))
    assert (result.third_level_promoted_prototypes,
            result.third_level_promoted_occurrences) == (4, 8)
    assert result.third_level_admitted_types == 2
    assert result.third_level_quotient_types == 1
    assert (result.fourth_level_promoted_prototypes,
            result.fourth_level_promoted_occurrences) == (1, 2)
    assert result.fourth_level_admitted_types == 0
    assert result.fourth_level_quotient_types == 0
    assert result.boundary_sparse_source_edges == 88
    assert result.boundary_sparse_retained_nodes == 16
    assert result.boundary_sparse_retained_edges == 15
    assert result.boundary_admitted_types_by_level == (8, 2, 0)
    assert result.boundary_quotient_types_by_level == (4, 1, 0)
    assert result.boundary_artifact_occurrences_by_level == (22, 8, 2)
    assert result.boundary_source_edges_by_level == (88, 18, 0)
    assert result.boundary_admitted_occurrence_multiplicities_by_level == (
        (2, 2, 2, 2, 2, 2, 2, 2), (2, 2), ())
    assert result.boundary_quotient_promotion_multiplicities_by_level == (
        (2, 2, 2, 2), (2,), ())
    assert not result.three_recursive_mined_levels_available
    assert not result.strict_stationary_audit_invoked
    assert not result.stationary
    assert not result.target_used


if __name__ == "__main__":
    test_six_patch_submacros_reach_two_positive_recursive_levels()
    print("recursive six-patch action submacros: all assertions passed")
