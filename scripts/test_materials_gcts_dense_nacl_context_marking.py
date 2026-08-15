#!/usr/bin/env python3

from materials_gcts_dense_nacl_context_marking_benchmark import evaluate


result = evaluate(shuffled_runs=7)
assert result.guarded_occurrence_domains_disjoint
assert result.identical_frozen_candidates
assert result.maximum_interaction_order == 2
assert result.target_global_frame_radius_unused_by_marking
assert not result.grammar_and_marking_fit_on_independent_train_cloud
assert result.evaluation_outer_shell_used_during_fit_or_ranking
assert result.equivariance_or_in_sample_diagnostic_only
assert result.matched_correct_novel_atoms > 0
assert not result.integrated_as_default_policy
assert not result.causal_gate_passed

print("dense NaCl incoming-context marking: assertions passed",
      "green" if result.causal_gate_passed else "red")
