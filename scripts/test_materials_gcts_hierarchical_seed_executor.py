#!/usr/bin/env python3
"""Focused control for target-blind exact hierarchy recognition/execution."""

from materials_gcts_generic import benchmark_systems
from materials_gcts_hierarchical_seed_executor import (
    FrozenHierarchyLevel, recognize_and_execute_frozen_hierarchy)
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_promoted_type_quotient import quotient_macro_supports
from materials_gcts_recurrent_macro_executor import ExecutionBoundary


def test_nacl_seed_recognizes_and_executes_frozen_l1_without_target():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    primitive = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(primitive, maximum_nodes=2)
    quotient = quotient_macro_supports(mined.macro_types)
    promoted = promote_macro_types(primitive, quotient.quotient_macros, level=1)
    result = recognize_and_execute_frozen_hierarchy(
        primitive, (FrozenHierarchyLevel(quotient, promoted),),
        nacl.species, nacl.positions,
        boundary=ExecutionBoundary((0., 0., 0.), 100.),
        maximum_waves=1, maximum_accepted_per_wave=8)
    assert result.primitive_occurrences > 0
    assert result.primitive_admitted_relations > 0
    assert result.levels[0].recognized_occurrences > 0
    assert result.levels[0].seed_atoms_covered > 0
    assert len(result.executions) == 1
    execution = result.executions[0][1]
    assert execution.exact_certificates
    assert not execution.target_used_for_proposals_or_ranking
    assert not result.target_api_present
    assert not result.target_used_for_recognition_or_execution


if __name__ == "__main__":
    test_nacl_seed_recognizes_and_executes_frozen_l1_without_target()
    print("hierarchical seed executor: passed")
