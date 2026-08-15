#!/usr/bin/env python3
"""Slow sealed transfer regression for the history-free hierarchy."""

from materials_gcts_iqc_reclustered_transfer_audit import evaluate


def test_reclustered_hierarchy_transfer_is_sealed_and_exact():
    result = evaluate()
    assert result.predeclared_patches == 8
    assert set(result.train_patch_ids).isdisjoint(result.heldout_patch_ids)
    assert len(result.train_patch_ids) == 5
    assert len(result.heldout_patch_ids) == 3
    assert result.raw_patch_domains_mutually_disjoint
    assert result.train_heldout_raw_ids_disjoint
    assert not result.heldout_used_for_fit_or_admission
    assert not result.family_phi_cell_used
    assert not result.target_labels_used

    assert result.train_complete_cover
    assert result.train_gap_atoms == 0
    assert (result.heldout_frozen_covered_atoms +
            result.heldout_explicit_gap_atoms == result.heldout_atoms)
    assert result.heldout_frozen_support_coverage == 1.0
    assert result.heldout_support_occurrences_patch_local
    assert (result.heldout_recognized_support_types <=
            result.frozen_support_types)
    assert result.heldout_witnessed_frozen_port_types <= result.frozen_port_types

    depth = result.train_positive_hierarchy_levels
    assert depth == len(result.train_quotient_types_by_level)
    assert depth == len(result.train_derivation_alternatives_by_level)
    assert depth == len(result.train_alternative_marking_samples_by_level)
    replay_depth = len(result.heldout_macro_types_replayed_by_level)
    assert replay_depth == len(result.heldout_macro_type_coverage_by_level)
    assert replay_depth == len(result.heldout_macro_occurrences_by_level)
    assert replay_depth == len(
        result.heldout_derivation_alternatives_replayed_by_level)
    assert replay_depth == len(
        result.heldout_derivation_alternative_occurrences_by_level)
    assert replay_depth == len(result.heldout_macro_atom_coverage_by_level)
    assert replay_depth == len(result.exact_replay_geometry_verified_by_level)
    assert all(result.exact_replay_geometry_verified_by_level)
    assert all(0.0 <= value <= 1.0
               for value in result.heldout_macro_type_coverage_by_level)
    assert all(0.0 <= value <= 1.0
               for value in result.heldout_macro_atom_coverage_by_level)
    assert result.transferred_positive_levels == sum(
        result.frozen_type_map_preserved_by_level)
    assert result.six_level_hierarchy_transfers == (
        result.transferred_positive_levels >= 6)

    # Durable scientific result: nearly all first-level exact productions
    # replay and cover every heldout atom, but three frozen types are absent.
    assert result.train_quotient_types_by_level[0] == 259
    assert result.heldout_macro_types_replayed_by_level[0] == 256
    assert result.heldout_macro_atom_coverage_by_level[0] == 1.0
    assert not result.frozen_type_map_preserved_by_level[0]
    assert result.transferred_positive_levels == 0
    assert not result.six_level_hierarchy_transfers


if __name__ == "__main__":
    test_reclustered_hierarchy_transfer_is_sealed_and_exact()
    print("sealed history-free hierarchy transfer: all assertions passed")
