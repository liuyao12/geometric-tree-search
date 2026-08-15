#!/usr/bin/env python3
"""Slow exact target-free six-patch induced-submacro regression."""

from materials_gcts_iqc_six_patch_action_submacro_benchmark import evaluate


def test_six_patch_corpus_has_exact_independent_submacro_recurrence():
    result = evaluate()
    assert result.corpus_digest == (
        "31ebd517c91dabc9df3e981fef7add0e7fb7ef1016128724e021b103d1c56858")
    assert result.training_atoms == 887
    assert result.source_patches == 6
    assert result.action_macros == 77
    assert result.action_macro_counts_by_patch == (12, 10, 12, 15, 13, 15)
    assert all(result.exact_action_node_cover_by_patch)
    assert result.connected_induced_candidates == 3844
    assert result.exact_canonical_classes == 3797
    assert result.rejected_insufficient_disjoint_evidence == 3750
    assert result.rejected_nonpositive_mdl == 0
    assert result.admitted_submacro_types == 47
    assert result.independent_patch_supported_types == 46
    assert result.independent_patch_support_histogram == ((1, 1), (2, 46))
    assert result.proof_occurrence_count_histogram == ((2, 47),)
    assert result.prototype_promotable_types == 47
    assert result.independently_supported_prototype_promotable_types == 46
    assert not result.executable_next_level_program_emitted
    assert result.recurrence_observed
    assert not result.hierarchy_stationarity_claimed
    assert not result.target_labels_stored
    assert not result.target_used


if __name__ == "__main__":
    test_six_patch_corpus_has_exact_independent_submacro_recurrence()
    print("six-patch target-free action submacros: all assertions passed")
