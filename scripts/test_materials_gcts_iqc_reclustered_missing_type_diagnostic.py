#!/usr/bin/env python3
"""Slow regression for the sealed first-level missing-type diagnosis."""

from materials_gcts_iqc_reclustered_missing_type_diagnostic import evaluate


def test_missing_types_share_a_rare_boundary_primitive_not_an_alternative():
    result = evaluate()
    assert result.train_heldout_patch_ids_disjoint
    assert result.heldout_support_isometry_novelty_atoms == 0
    assert not result.family_phi_cell_labels_used
    assert result.missing_direct_type_ids == (184, 185, 252)
    assert len(result.missing_types) == 3
    for item in result.missing_types:
        assert item.absent_child_types == (49,)
        assert item.absent_child_train_occurrences == (2,)
        assert item.absent_child_train_patch_ids == ((2,),)
        assert item.absent_child_support_kinds == ("repeated",)
        assert item.absent_child_atom_counts == (23,)
        assert item.direct_graph_embeddings_considered == 0
        assert item.direct_exact_occurrences == 0
        assert item.heldout_backoff_occurrences == 0
        assert item.heldout_exact_alternatives_replayed == 0
        assert item.frozen_primitive_absent_in_heldout
        assert item.port_novelty
        assert not item.alternative_derivation_mismatch
        assert item.insufficient_multiplicity
        assert item.boundary_crop_artifact_likely

    backoff = result.backoff
    assert backoff.train_types == 259
    assert backoff.direct_types_with_one_occurrence == 256
    assert backoff.direct_types_with_two_occurrences == 256
    assert backoff.semantic_types_with_one_occurrence == 256
    assert backoff.semantic_types_with_two_occurrences == 256
    assert backoff.ambiguous_atom_unions == 0
    assert backoff.assignment_precision == 1.0
    assert backoff.semantic_type_coverage == 256 / 259
    assert backoff.strict_transfer_type_coverage == 256 / 259
    assert not backoff.all_type_ids_semantically_covered
    assert not backoff.all_type_ids_transferable_with_two_occurrences
    assert backoff.train_fitted_mapping_only
    assert not backoff.heldout_used_for_tuning_or_admission
    assert backoff.exact_action_identity_preserved


if __name__ == "__main__":
    test_missing_types_share_a_rare_boundary_primitive_not_an_alternative()
    print("sealed missing-type diagnostic: all assertions passed")
