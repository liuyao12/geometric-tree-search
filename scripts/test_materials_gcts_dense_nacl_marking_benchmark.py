#!/usr/bin/env python3

from materials_gcts_dense_nacl_marking_benchmark import evaluate


result = evaluate(shuffled_runs=7)
assert result.identical_frozen_candidates
assert result.marking_fit_train_ports_only
assert result.global_radius_direction_target_unused_by_marking
assert result.marked.correct_novel_atoms >= result.matched_correct_novel_atoms
assert result.unmarked.correct_novel_atoms >= result.matched_correct_novel_atoms
assert result.marked.proposals < result.unmarked.proposals
assert result.marked.precision > result.unmarked.precision
# It beats the old deterministic ordering, but not the within-parent shuffled
# controls. Keep the proposed marking out of the default growth policy.
assert not result.in_sample_reconstruction_gate_passed
assert not result.independent_outer_shell
assert not result.integrated_as_default_policy

print("dense NaCl causal marking: all assertions passed")
