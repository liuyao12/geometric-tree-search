#!/usr/bin/env python3
"""Durable red gate for target-blind Cd--Yb hierarchy execution."""

from materials_gcts_cdyb_hierarchical_seed_execution_benchmark import evaluate


def test_cdyb_deep_hierarchy_cannot_seed_disjoint_autonomous_nucleus():
    result = evaluate()
    assert result.train_windows == 5 and result.train_atoms == 2385
    assert result.frozen_positive_levels == 9
    assert result.quotient_types_by_level == (80, 36, 22, 15, 8, 6, 4, 2, 1, 0)
    assert result.seed_atoms == 478
    assert result.target_atoms == 2696 and result.outer_atoms == 2218
    assert result.minimum_train_eval_center_separation > result.train_target_radii_sum
    assert result.train_eval_raw_id_intersection == 0
    assert result.spatial_domains_disjoint
    assert result.primitive_seed_occurrences == 276
    assert result.primitive_seed_admitted_relations == 500
    assert result.recognized_occurrences_by_level == (0,)
    assert result.recognized_types_by_level == (0,)
    assert result.recognized_seed_coverage_by_level == (0,)
    assert not result.executed_levels
    assert result.highest_recognized_level == 0
    assert result.highest_executed_level == 0
    assert not result.any_higher_level_exterior_emission
    assert result.every_emission_exactly_certified
    assert result.certification_vacuous_no_emissions
    assert result.target_factory_called_after_execution
    assert not result.target_used_for_recognition_or_execution
    assert not result.family_cell_source_site_or_expected_scale_used
    assert not result.autonomous_hierarchical_gate_passed


if __name__ == "__main__":
    test_cdyb_deep_hierarchy_cannot_seed_disjoint_autonomous_nucleus()
    print("CdYb hierarchical seed execution benchmark: assertions passed")
