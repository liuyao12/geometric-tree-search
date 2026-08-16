#!/usr/bin/env python3
"""Slow causal regression for the disjoint R11 recurrent-macro stall."""

from materials_gcts_iqc_recurrent_stall_diagnostic import evaluate


def test_r11_stall_is_batch_schedule_depth_not_missing_frozen_semantics():
    result = evaluate()
    assert result.baseline.accepted_by_wave == (16, 8, 0)
    assert result.cap_eight.accepted_by_wave == (8, 8, 8, 0)
    assert result.baseline.proposed_novel_atoms == \
        result.cap_eight.proposed_novel_atoms == 148
    assert result.baseline.correct_novel_atoms_posthoc == \
        result.cap_eight.correct_novel_atoms_posthoc == 136
    assert result.wave_count_is_batch_scheduling_dependent
    assert result.early_commit_path_is_causal
    assert result.third_wave_reachable_with_same_frozen_grammar

    assert result.baseline.frontier_nodes_without_outgoing_production == 0
    assert not result.selected_grammar_absolute_frontier_exhaustion
    assert not result.unfiltered_grammar_improves_seed_cover
    assert not result.unfiltered_grammar_improves_reachable_union
    assert not result.missing_recurrent_exterior_types_are_causal

    assert not result.seed_macro_cover_complete
    assert result.larger_seed_improves_macro_frontier
    assert not result.seed_coverage_is_cause_of_depth_two_stall
    assert result.baseline.wrong_placements_by_wave_posthoc[:2] == (8, 4)
    assert not result.wrong_placement_blocking_causally_established

    assert not result.derivation_boundary_recovery_improves_precision_or_recall
    assert not result.recovery_integrated
    assert not result.target_used_to_choose_or_rank_actions
    assert all(not arm.target_used_during_execution for arm in (
        result.baseline, result.cap_eight, result.consensus_half,
        result.all_exact_derivation_boundaries,
        result.all_exact_derivation_boundaries_consensus_half,
        result.unfiltered_frozen_macro_vocabulary,
        result.larger_seed_radius_eight))


if __name__ == "__main__":
    test_r11_stall_is_batch_schedule_depth_not_missing_frozen_semantics()
    print("IQC recurrent stall diagnostic: all assertions passed")
