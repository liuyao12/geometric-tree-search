#!/usr/bin/env python3

from materials_gcts_nacl_generator_cell_audit import evaluate


result = evaluate()
assert result.base.macro_children == result.base.learned_child_offset_count
assert result.base.macro_internal_directed_ports > result.base.macro_children
assert result.base.independent_macro_occurrences >= 2
assert result.base.macro_mdl_saving > 0
assert result.base.stationary
assert result.permutation_invariant
assert result.proper_se3_invariant
assert result.amorphous_generators_rejected
assert result.iqc_generators_rejected
assert result.positions_only_grid_oracle_stationary
assert result.full_graph_recovers_learned_cell
assert not result.sparse_reduction_discarded_cell
assert result.ternary_control_radix > 1
assert result.ternary_control_radix != result.base.learned_radix
assert result.ternary_control_children == (
    result.ternary_control_radix ** result.base.learned_dimension)
assert result.strong_stationarity_passed
assert result.passed

print("NaCl full-relation generator cell: all assertions passed")
