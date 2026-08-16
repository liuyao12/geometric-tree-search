#!/usr/bin/env python3

from materials_gcts_cdyb_partial_vocabulary_deployment import evaluate


def test_partial_frozen_vocabulary_continues_without_claiming_dormant_types():
    result = evaluate()
    assert result.train_heldout_raw_id_intersection == 0
    assert result.frozen_levels == 9
    assert result.attempted_levels == 5
    assert result.positive_active_depth == 4
    assert result.active_types_by_level == (53, 20, 8, 2, 0)
    assert result.dormant_types_by_level == (27, 16, 14, 13, 8)
    assert result.occurrences_by_level == (92, 26, 8, 2, 0)
    assert result.residual_atoms_by_level == (399, 514, 645, 789, 959)
    assert tuple(item.minimum_active_namespaces for item in result.levels) == (
        1, 1, 1, 1, 0)
    assert tuple(item.minimum_active_atom_independent_occurrences
                 for item in result.levels) == (1, 1, 1, 1, 0)
    assert all(item.active_types + item.dormant_types == item.frozen_types
               for item in result.levels)
    assert all(item.complete_representation_certificate
               for item in result.levels)
    assert not result.dormant_types_claimed_transferred
    assert not result.vocabulary_refit_or_renumbered_on_heldout
    assert result.heldout_reencoding_only
    assert not result.autonomous_growth_or_emission
    assert result.all_exact_certificates
    assert result.leakage_safe_partial_deployment
    assert result.stopped_reason == (
        "no active exact occurrences can seed the next level")


if __name__ == "__main__":
    test_partial_frozen_vocabulary_continues_without_claiming_dormant_types()
    print("CdYb partial frozen-vocabulary deployment: assertions passed")
