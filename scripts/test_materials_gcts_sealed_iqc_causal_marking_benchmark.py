#!/usr/bin/env python3
"""Real sealed-IQC causal incoming-port ablation assertions."""

from materials_gcts_sealed_iqc_causal_marking_benchmark import evaluate


def main() -> None:
    result = evaluate()
    assert result.training_atoms == 887
    assert result.evaluation_seed_atoms == 223
    assert result.scoring_target_atoms == 877
    assert result.train_target_raw_id_intersection == 0
    assert result.train_evaluation_center_separation > result.sum_train_target_radii
    assert result.spatial_domains_disjoint
    assert result.recognized_seed_occurrences == 20
    assert result.maximum_interaction_order == 2
    assert result.candidate_actions == 309
    assert result.attempted_poses == 1317
    assert result.exact_candidate_actions == 232
    assert result.union_correct_novel_target_atoms == 425
    assert result.scorer_calls == 1
    assert result.scorer_called_after_candidate_freeze
    assert result.grammar_fit_on_training_only
    assert result.marking_fit_on_causal_training_relations_only
    assert not result.target_used_for_candidate_generation_or_ranking
    assert result.ablation.shuffled_runs == 31
    assert result.ablation.candidate_set_identical
    assert result.ablation.matched_correct_novel_atoms == 425
    assert result.seed_occurrences_with_incoming_context == 16
    assert result.candidates_with_incoming_context == 258
    assert result.candidate_exact_context_seen_in_training == 4
    assert result.abstract_candidate_exact_context_seen_in_training == 4
    assert result.abstract_candidate_backoff_context_seen_in_training == 45
    assert result.geometry_selection.selected_on_training_only
    assert result.geometry_selection.guarded_domains_disjoint
    assert result.geometry_selection.specifications_compared == 144
    assert result.geometry_selection.spec.include_axis_translation_invariant
    assert result.geometry_selection.spec.include_incoming_outgoing_angle
    assert result.exact_candidate_ids_preserved
    assert result.bounded_geometry_features_present
    assert not result.ablation.marked_beats_unmarked
    assert not result.ablation.marked_beats_shuffle_median
    assert result.ablation.empirical_work_p_value == 1.0
    assert not result.ablation.benchmark_passed
    assert not result.benchmark_passed
    print("real sealed IQC causal marking benchmark: assertions passed")


if __name__ == "__main__":
    main()
