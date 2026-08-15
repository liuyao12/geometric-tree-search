#!/usr/bin/env python3
"""Slow exact target-free six-patch induced-submacro regression."""

from materials_gcts_iqc_six_patch_action_submacro_benchmark import evaluate


def test_six_patch_corpus_has_exact_independent_submacro_recurrence():
    result = evaluate()
    assert result.corpus_digest == (
        "8645b480d2e1caa1a620d3541df8b37a06213b27707e085bdb0d62bd70d8dfe8")
    assert result.training_atoms == 887
    assert result.source_patches == 6
    assert result.action_macros == 71
    assert result.action_macro_counts_by_patch == (12, 9, 13, 13, 13, 11)
    assert all(result.exact_action_node_cover_by_patch)
    assert result.connected_induced_candidates == 4023
    assert result.exact_canonical_classes == 4012
    assert result.rejected_insufficient_disjoint_evidence == 4001
    assert result.rejected_nonpositive_mdl == 0
    assert result.admitted_submacro_types == 11
    assert result.independent_patch_supported_types == 10
    assert result.independent_patch_support_histogram == ((1, 1), (2, 10))
    assert result.proof_occurrence_count_histogram == ((2, 11),)
    assert result.prototype_promotable_types == 11
    assert result.independently_supported_prototype_promotable_types == 10
    assert not result.executable_next_level_program_emitted
    assert result.recurrence_observed
    assert not result.hierarchy_stationarity_claimed
    assert not result.target_labels_stored
    assert not result.target_used


if __name__ == "__main__":
    test_six_patch_corpus_has_exact_independent_submacro_recurrence()
    print("six-patch target-free action submacros: all assertions passed")
