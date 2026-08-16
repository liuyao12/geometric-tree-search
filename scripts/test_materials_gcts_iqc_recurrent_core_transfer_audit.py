#!/usr/bin/env python3
"""Slow max-five IQC recurrent-core transfer regression."""

from materials_gcts_iqc_recurrent_core_transfer_audit import evaluate


def test_max_five_recurrent_core_transfers_without_boundary_types():
    result = evaluate(maximum_nodes=5)
    assert result.training_patches == 5
    assert result.heldout_patches == 3
    assert result.strict_majority_threshold == 3
    assert result.train_quotient_types == 520
    assert result.selected_recurrent_types == 148
    assert result.rejected_nonrecurrent_types == 372
    assert result.selected_type_ids_preserved
    assert result.patch2_only_types_rejected
    assert result.rare_primitive49_type_ids
    assert set(result.rare_primitive49_type_ids).issubset(
        result.patch2_only_train_type_ids)
    assert result.rare_primitive49_types_rejected

    assert result.train_atoms == 2048
    assert result.selected_train_covered_atoms == 1890
    assert result.exact_residual_atom_terminals == 158
    assert len(result.residual_atom_indices) == 158
    assert len(set(result.residual_atom_indices)) == 158
    assert len(result.train_representation_certificate_digest) == 64
    assert result.complete_train_representation

    assert result.heldout_atoms == 1248
    assert result.selected_types_with_two_exact_heldout_occurrences == 148
    assert result.selected_type_transfer_coverage == 1.0
    assert result.heldout_exact_macro_occurrences == 1495
    assert result.heldout_atoms_covered_by_selected_types == 1220
    assert result.heldout_atom_coverage == 1220 / 1248
    assert result.exact_proper_se3_replay
    assert result.all_selected_types_transfer_with_two_occurrences
    assert not result.selector_read_heldout
    assert not result.target_family_phi_cell_labels_used


if __name__ == "__main__":
    test_max_five_recurrent_core_transfers_without_boundary_types()
    print("max-five recurrent-core transfer: all assertions passed")
