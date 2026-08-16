#!/usr/bin/env python3

from materials_gcts_cdyb_hierarchical_growth_design import evaluate


def test_cdyb_hierarchical_growth_design_is_sealed_and_honest():
    result = evaluate()
    assert result.eval_center == (35., 30., 20.)
    assert result.seed_radius == 14.
    assert result.target_radius == 25.
    assert result.train_target_raw_id_intersection == 0
    assert result.spatial_domains_disjoint
    assert result.oracle_target_ball_unclipped
    assert result.frozen_hierarchy_levels == 4
    assert result.target_factory_called_after_all_candidate_traces_frozen
    assert result.candidate_sets_target_blind_and_digest_frozen
    assert result.same_train_seed_boundary_for_all_arms
    assert not result.heldout_target_used_for_fit_ranking_or_branch_selection
    assert result.benchmark_is_design_not_growth_claim
    assert result.arms[0].arm == "primitive-port"
    assert result.seed_active_types_by_level == (0, 0, 0, 0)
    assert result.seed_occurrences_by_level == (0, 0, 0, 0)
    assert result.executable_hierarchy_levels == ()
    assert result.common_matched_correct_atom_budget == 0
    assert result.arms[0].matched_work is None
    assert all(not arm.executable for arm in result.arms[1:])
    assert result.exact_blocker.startswith("seed recognition blocker")
    assert all(not arm.target_used_during_compile_or_execution
               for arm in result.arms)


if __name__ == "__main__":
    test_cdyb_hierarchical_growth_design_is_sealed_and_honest()
    print("CdYb hierarchical growth design: assertions passed")
