#!/usr/bin/env python3

from materials_gcts_macro_width_safety_audit import evaluate


result = evaluate()
assert result.widths == (4, 5, 8)
assert len(result.cases) == 6
assert result.all_finite
assert result.all_permutation_invariant
assert result.all_proper_se3_invariant
assert result.amorphous_stationarity_rejected
assert result.nacl_eight_child.rooted_candidates_width_2_to_8[-1] > 0
assert result.nacl_eight_child.canonical_permutation_work_width_8 > (
    result.nacl_eight_child.canonical_permutation_work_width_5)
assert result.nacl_eight_child.width_8_full_geometry_run
assert not result.nacl_eight_child.eight_child_stationary_rule_learned
assert result.passed

print("macro width safety controls: all assertions passed")
