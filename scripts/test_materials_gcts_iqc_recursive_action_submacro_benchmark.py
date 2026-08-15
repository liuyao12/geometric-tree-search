#!/usr/bin/env python3
"""Slow regression for exact action-submacro recursive promotion."""

from materials_gcts_iqc_recursive_action_submacro_benchmark import evaluate


def test_six_patch_submacros_reach_two_positive_recursive_levels():
    result = evaluate()
    assert result.corpus_digest == (
        "31ebd517c91dabc9df3e981fef7add0e7fb7ef1016128724e021b103d1c56858")
    assert result.initial_admitted_submacro_types == 47
    assert (result.promoted_prototypes,
            result.promoted_dense_occurrences) == (47, 94)
    assert result.namespaced_support_atoms == 310
    assert (result.promoted_overlap_ports,
            result.promoted_overlap_relations) == (1694, 3388)
    assert (result.promoted_boundary_ports,
            result.promoted_boundary_relations) == (1352, 2704)
    assert (result.sparse_source_nodes, result.sparse_source_edges) == (94, 1694)
    assert (result.sparse_retained_nodes,
            result.sparse_retained_edges) == (12, 9)
    assert result.next_level_candidates == 36
    assert result.next_level_exact_classes == 30
    assert result.next_level_admitted_types == 6
    assert result.next_level_quotient_types == 3
    assert result.next_level_exact_quotient_classes == (
        (0, 1), (2, 3), (4, 5))
    assert (result.third_level_promoted_prototypes,
            result.third_level_promoted_occurrences) == (3, 6)
    assert result.third_level_admitted_types == 2
    assert result.third_level_quotient_types == 1
    assert (result.fourth_level_promoted_prototypes,
            result.fourth_level_promoted_occurrences) == (1, 2)
    assert result.fourth_level_admitted_types == 0
    assert result.fourth_level_quotient_types == 0
    assert not result.three_recursive_mined_levels_available
    assert not result.strict_stationary_audit_invoked
    assert not result.stationary
    assert not result.target_used


if __name__ == "__main__":
    test_six_patch_submacros_reach_two_positive_recursive_levels()
    print("recursive six-patch action submacros: all assertions passed")
