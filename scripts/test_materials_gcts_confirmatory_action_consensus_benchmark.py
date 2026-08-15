#!/usr/bin/env python3
"""One-shot confirmatory action-consensus benchmark assertions."""

from materials_gcts_confirmatory_action_consensus_benchmark import evaluate


def main() -> None:
    result = evaluate()
    assert result.training_atoms == 887
    assert result.seed_atoms > 0 and result.target_atoms > result.seed_atoms
    assert result.train_target_raw_id_intersection == 0
    assert result.training_center_norm_squared == 256.0
    assert result.confirmatory_center_norm_squared == 330.0
    assert result.spatial_domains_disjoint
    assert result.frozen_candidates == 274
    assert result.rejected_outside_public_boundary > 0
    assert result.public_radial_boundary_used_before_labels
    assert result.frozen_budget == 100
    assert result.frozen_consensus_weight == 1.0
    assert result.frozen_log_frequency_weight == 1.0
    assert result.exploratory_rule_center == (8.0, 14.0, 7.0)
    assert not result.confirmatory_labels_used_for_rule_or_budget
    assert result.combined.exact_actions > result.frequency_only.exact_actions
    assert result.combined.exact_actions > result.consensus_only.exact_actions
    assert (result.combined.wrong_emitted_site_counts <
            result.frequency_only.wrong_emitted_site_counts)
    assert (result.combined.wrong_emitted_site_counts <
            result.consensus_only.wrong_emitted_site_counts)
    assert result.shuffled_runs == 31
    assert result.empirical_exact_action_p_value <= .05
    assert result.empirical_wrong_site_p_value <= .05
    assert result.empirical_matched_work_p_value <= .05
    assert (result.combined_matched_work.proposal_checks +
            result.combined_matched_work.geometric_backtracks <
            result.minimum_shuffled_matched_total_work)
    assert result.candidate_ids_and_actions_identical_across_arms
    assert result.every_shuffle_preserves_candidate_degree
    assert result.every_shuffle_preserves_site_degree
    assert result.rule_and_budget_frozen_before_confirmation
    assert result.target_constructed_after_candidates_and_controls
    assert not result.target_used_for_candidate_generation_features_or_ranking
    assert result.confirmatory_gate_passed
    print("confirmatory IQC action consensus: assertions passed")


if __name__ == "__main__":
    main()
