#!/usr/bin/env python3

from materials_gcts_cdyb_frozen_hierarchy_transfer_audit import evaluate


def test_cdyb_frozen_hierarchy_transfer_is_exact_reencoding_only():
    result = evaluate()
    assert result.train_windows == 5
    assert result.heldout_windows == 2
    assert result.train_atoms == 2385
    assert result.heldout_atoms == 959
    assert result.heldout_atoms_by_window == (500, 459)
    assert result.train_heldout_raw_id_intersection == 0
    assert result.heldout_raw_domains_disjoint
    assert result.spatial_domains_disjoint
    assert result.frozen_positive_levels == 9
    assert result.selected_types_by_level == (80, 36, 22, 15, 8, 6, 4, 2, 1)
    assert result.attempted_levels == 5
    assert result.transferred_types_by_level == (53, 20, 8, 2, 0)
    assert result.occurrences_by_level == (92, 26, 8, 2, 0)
    assert result.covered_atoms_by_level == (560, 445, 314, 170, 0)
    assert result.residual_atoms_by_level == (399, 514, 645, 789, 959)
    assert result.atom_coverage_by_level == (
        560 / 959, 445 / 959, 314 / 959, 170 / 959, 0.)
    assert result.minimum_namespaces_by_level == (0, 0, 0, 0, 0)
    assert result.minimum_independent_occurrences_by_level == (0, 0, 0, 0, 0)
    assert len(result.transferred_levels) == result.attempted_levels
    assert all(result.exact_replay_by_level)
    assert all(result.complete_representation_by_level)
    assert all(item.partial_deployment_safe
               for item in result.transferred_levels[:-1])
    assert not result.transferred_levels[-1].partial_deployment_safe
    assert all(item.active_frozen_type_ids
               for item in result.transferred_levels[:-1])
    assert all(item.inactive_frozen_type_ids
               for item in result.transferred_levels[:-1])
    assert result.transferred_levels[-1].active_frozen_type_ids == ()
    assert result.namespaces_preserved
    assert result.stopped_reason.startswith("fail-closed")
    assert result.heldout_reencoding_only
    assert not result.autonomous_growth_or_emission
    assert not result.heldout_used_for_fit_admission_or_branch_selection
    assert not result.source_sites_family_cell_or_expected_scale_used


if __name__ == "__main__":
    test_cdyb_frozen_hierarchy_transfer_is_exact_reencoding_only()
    print("CdYb frozen hierarchy transfer audit: assertions passed")
