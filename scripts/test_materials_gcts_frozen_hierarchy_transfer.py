#!/usr/bin/env python3
"""Focused contracts for strict frozen hierarchy deployment."""

from materials_gcts_iqc_strict_hierarchy_transfer_benchmark import evaluate


def test_strict_iqc_transfer_is_sealed_and_exact():
    result = evaluate(maximum_levels=3)
    assert result.attempted_levels >= 1
    assert (result.transferred_types_by_level ==
            result.train_recurrent_types_by_level[:result.attempted_levels])
    assert result.patch_namespaces_preserved
    assert result.all_type_maps_frozen
    assert result.all_relations_train_admitted
    assert result.heldout_reencoding
    assert not result.autonomous_growth
    assert all(result.exact_replay_by_level)
    assert all(item.complete_representation_certificate
               for item in result.transferred_levels)
    assert all(item.raw_atom_digest == item.exact_representation_digest
               for item in result.transferred_levels)
    assert all(item.every_frozen_type_transferred
               for item in result.transferred_levels)
    assert all(item.minimum_distinct_namespaces_per_frozen_type >= 2
               for item in result.transferred_levels)
    assert all(item.minimum_independent_occurrences_per_frozen_type >= 2
               for item in result.transferred_levels)
    assert not result.heldout_used_for_fit_admission_or_branch_selection
    assert not result.target_labels_used
    assert not result.family_phi_cell_used
    assert all(0 <= value <= 1 for value in result.atom_coverage_by_level)
    assert all(count >= 0 for count in result.gap_atoms_by_level)
if __name__ == "__main__":
    test_strict_iqc_transfer_is_sealed_and_exact()
    print("strict frozen hierarchy transfer: all assertions passed")
