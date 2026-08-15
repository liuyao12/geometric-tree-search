#!/usr/bin/env python3
"""Slow fieldwise audit of the re-clustered six-patch hierarchy."""

from materials_gcts_iqc_action_graph_corpus import _build_with_executions
from materials_gcts_iqc_reclustered_growth_corpus import _pack, _recursive
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_stationary_field_ablation import audit_stationary_fields


_, executions, _ = _build_with_executions()
species, positions, patch_by_index, _ = _pack(executions)
levels = _recursive(
    compile_irregular_port_program(species, positions), True,
    patch_by_index, 3)[8]
result = audit_stationary_fields(levels, tolerance=1e-5)

assert result.levels == (0, 1, 2, 3, 4, 5)
assert result.records_by_level == (73, 17, 5, 3, 2, 1)
assert result.fields[0].consecutive_three_level_intersections == (
    0, 1, 0, 0)
assert result.fields[1].adjacent_intersections == (0, 2, 0, 0, 0)
assert result.fields[3].adjacent_intersections == (0, 1, 0, 0, 0)
assert result.fields[4].adjacent_intersections == (0, 0, 0, 0, 0)
assert result.first_failing_field == "species-set+chirality"
assert result.reusable_pre_pose_three_level_keys == 0
assert result.topology_three_level_maximum_minimum_occurrences == 2
assert not result.topology_three_level_meets_sixteen_deployments_each_level
assert result.population_adjacent_compatible_pairs == 0
assert result.population_three_level_equal_substitution_triples == 0
assert result.population_substitution_matrices == ()
assert not result.strict_stationarity_claimed
assert not result.target_family_phi_cell_used

print("re-clustered stationary field ablation: all assertions passed")
