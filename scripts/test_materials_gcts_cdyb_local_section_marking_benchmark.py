#!/usr/bin/env python3
"""Slow regression for bounded local Cd--Yb GCTS marking."""

from materials_gcts_cdyb_local_section_marking_benchmark import evaluate


def test_cdyb_local_section_marking():
    result = evaluate(31)
    assert result.train_atoms == 969
    assert result.training_selected_candidate_precision == 1.0
    assert 2.11 < result.learned_close_distance_cutoff_nn < 2.12
    assert result.learned_minimum_close_connection_witnesses == 5
    assert result.marking_domain_order == 1
    assert result.evaluation_nuclei == 2
    assert result.all_train_and_eval_domains_pairwise_disjoint
    assert result.marked.nuclei[0].accepted_per_wave == (
        3, 18, 9, 35, 5, 1, 0)
    assert result.marked.nuclei[0].correct_atoms == 178
    assert result.marked.nuclei[0].wrong_atoms == 0
    assert result.marked.nuclei[1].accepted_per_wave == (
        2, 12, 6, 4, 10, 14, 0)
    assert result.marked.nuclei[1].correct_atoms == 117
    assert result.marked.nuclei[1].wrong_atoms == 0
    assert result.marked.total_correct_atoms == 295
    assert result.marked.aggregate_precision == 1.0
    assert result.unmarked.total_wrong_atoms == 83
    assert result.shuffle_trials == 31
    assert result.marked_reach_empirical_p <= .05
    assert result.identical_first_wave_candidates_all_policies
    assert result.all_traces_frozen_before_evaluation_targets
    assert not result.target_labels_used_during_fit_or_execution
    assert not result.uses_absolute_position_direction_family_cell_potential_or_source_sites
    assert result.exact_promoted_action_macros > 0
    assert result.recurring_three_wave_macro_signatures == 0
    assert result.causal_local_marking_gate_passed
    assert not result.stationary_or_exponential_growth_claimed


if __name__ == "__main__":
    test_cdyb_local_section_marking()
    print("CdYb bounded local-section marking benchmark passed")
