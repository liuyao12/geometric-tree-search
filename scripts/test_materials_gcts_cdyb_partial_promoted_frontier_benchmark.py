#!/usr/bin/env python3

from materials_gcts_cdyb_partial_promoted_frontier_benchmark import evaluate


def test_cdyb_partial_promoted_frontier_is_sealed_and_finite():
    result = evaluate()
    assert result.train_atoms == 2385
    assert result.seed_atoms == 478
    assert result.lower_seed_occurrences > 0
    assert result.lower_seed_occurrences == 276
    assert result.frozen_parent_types == 80
    assert result.frozen_derivation_alternatives == 181
    assert result.frame_hypotheses == 274
    assert result.insufficient_geometric_witness_hypotheses == 0
    assert result.internal_port_rejections == 0
    assert result.child_coverage_rejections == 162
    assert result.one_child_missing_port_rejections == 0
    assert result.collision_rejections == 30
    assert result.redundant_completion_rejections == 0
    assert result.public_boundary_rejections == 0
    assert result.ambiguous_completion_signatures == 0
    assert result.partial_completion_candidates == 82
    assert result.posthoc_exact_completion_candidates == 6
    assert result.posthoc_wrong_completion_candidates == 76
    assert result.emitted_atoms_union == 333
    assert result.candidates_with_two_or_more_admitted_port_connected_witnesses == \
        0
    assert result.candidate_digest == \
        "279ec8d5dcdff277bce6297505373903b866dc947c09808eec3777bd2335d379"
    assert len(result.candidate_digest) == 64
    assert result.train_target_raw_id_intersection == 0
    assert result.spatial_domains_disjoint
    assert result.oracle_target_ball_unclipped
    assert result.target_opened_after_candidate_trace_frozen
    assert not result.target_used_for_candidate_enumeration_or_ranking
    assert not result.family_cell_scale_or_origin_heuristic_used


if __name__ == "__main__":
    test_cdyb_partial_promoted_frontier_is_sealed_and_finite()
    print("CdYb partial promoted frontier: passed")
