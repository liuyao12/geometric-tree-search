#!/usr/bin/env python3
"""Slow history-free six-patch re-clustering regression."""

from materials_gcts_iqc_reclustered_growth_corpus import evaluate


def test_reclustering_grown_clouds_improves_recurrence_depth():
    result = evaluate()
    assert len(result.corpus_digest) == 64
    assert result.patches == 6
    assert result.maximum_nodes == 3
    assert len(result.initial_atoms_by_patch) == result.patches
    assert all(final - initial == novel and novel > 0
               for initial, final, novel in zip(
                   result.initial_atoms_by_patch, result.final_atoms_by_patch,
                   result.novel_atoms_by_patch))
    assert result.pooled_atoms == sum(result.final_atoms_by_patch)
    assert result.complete_cover
    assert result.repeated_support_types > 0
    assert result.repeated_support_occurrences == result.primitive_occurrences
    assert result.repeated_covered_atoms + result.gap_atoms == result.pooled_atoms
    assert result.gap_types > 0 and result.gap_atoms > 0
    assert result.every_support_occurrence_patch_local
    assert result.every_macro_occurrence_patch_local
    assert result.primitive_prototypes > 0 and result.primitive_ports > 0
    for admitted, quotients, occurrences in (
            (result.overlap_admitted_types_by_level,
             result.overlap_quotient_types_by_level,
             result.overlap_artifact_occurrences_by_level),
            (result.boundary_admitted_types_by_level,
             result.boundary_quotient_types_by_level,
             result.boundary_artifact_occurrences_by_level)):
        assert len(admitted) == len(quotients) == len(occurrences)
        assert admitted[-1] == quotients[-1] == 0
        assert all(source >= quotient >= 0
                   for source, quotient in zip(admitted, quotients))
        assert all(left >= right for left, right in zip(
            occurrences, occurrences[1:]))
    assert result.reclustered_maximum_proof_multiplicity > (
        result.action_history_maximum_dense_occurrence_multiplicity)
    assert result.reclustered_positive_quotient_levels == sum(
        value > 0 for value in result.boundary_quotient_types_by_level)
    assert all(child_count <= result.maximum_nodes
               for levels in (result.overlap_child_count_histograms,
                              result.boundary_child_count_histograms)
               for histogram in levels for child_count, _ in histogram)
    assert len(result.overlap_mining_seconds_by_level) == len(
        result.overlap_admitted_types_by_level)
    assert len(result.boundary_mining_seconds_by_level) == len(
        result.boundary_admitted_types_by_level)
    assert result.initial_overlap_boundary_mining_reused
    assert result.reclustering_improves_maximum_proof_multiplicity
    assert result.reclustering_improves_positive_hierarchy_depth
    assert result.strict_stationary_audit_invoked
    assert (result.stationary_adapted_records +
            result.stationary_adaptation_rejections ==
            sum(result.boundary_quotient_types_by_level))
    assert result.stationary_eligible_records <= result.stationary_adapted_records
    if result.stationary_witnesses:
        assert result.stationary
        assert result.stationary_first_two_levels_materialized
    else:
        assert not result.stationary
        assert result.progressive_first_zero_field is not None
    progressive = (
        result.progressive_topology_intersections,
        result.progressive_chemistry_chirality_intersections,
        result.progressive_directed_port_intersections,
        result.progressive_normalized_pose_intersections,
        result.progressive_population_substitution_intersections)
    assert all(len(counts) == len(result.progressive_stationary_windows)
               for counts in progressive)
    assert all(all(stronger <= weaker
                   for stronger, weaker in zip(right, left))
               for left, right in zip(progressive, progressive[1:]))
    assert not result.target_used
    assert not result.family_or_cell_used
    assert not result.action_history_ids_used


if __name__ == "__main__":
    test_reclustering_grown_clouds_improves_recurrence_depth()
    print("history-free grown-patch reclustering: all assertions passed")
