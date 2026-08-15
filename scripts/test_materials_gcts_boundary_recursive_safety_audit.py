#!/usr/bin/env python3

from materials_gcts_boundary_recursive_safety_audit import evaluate


result = evaluate()
assert len(result.cases) == 3
assert result.all_boundary_edges_train_witnessed
assert result.all_candidate_graphs_finite
assert result.all_default_paths_byte_semantics_preserved
assert result.amorphous_stationary_recursion_rejected
assert result.six_patch_depth.third_binary_promotion_mathematically_starved
assert result.six_patch_depth.boundary_recursion_terminated
assert not result.six_patch_depth.stationary_claimed
assert not result.six_patch_depth.target_used
# Metamorphic checks are scientific gates, not digest-only comparisons.
assert result.all_input_permutations_invariant
assert result.all_proper_rigid_transforms_invariant
assert result.passed

print("boundary recursive safety audit: contract assertions passed")
