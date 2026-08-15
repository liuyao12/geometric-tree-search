#!/usr/bin/env python3

from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_recursive_port_hierarchy import (
    HierarchyCallbacks, HierarchyMacroSummary, MinedHierarchyLevel,
    drive_recursive_port_hierarchy, normalized_macro_signature,
    real_first_level_callbacks)
from materials_gcts_port_graph_macros import BoundarySlot, MacroEdge
from types import SimpleNamespace


def _synthetic_callbacks():
    stationary = (
        "finite_oriented_port_substitution", (0, 1),
        ((0, 1, 0, 1, (5, 8)),), ())
    changed_ids_but_normalized = stationary
    levels = (
        MinedHierarchyLevel(7, (
            HierarchyMacroSummary(12, 2, 9, stationary, True),)),
        MinedHierarchyLevel(3, (
            HierarchyMacroSummary(
                31, 2, 14, changed_ids_but_normalized, True),)),
        MinedHierarchyLevel(2, (
            HierarchyMacroSummary(70, 3, 0, ("rejected",)),)),
    )

    def mine(artifact, level):
        assert artifact == level
        return levels[level]

    def promote(artifact, mined, level):
        assert artifact == level and mined is levels[level]
        return level + 1

    return HierarchyCallbacks(mine, promote)


def test_injectable_driver_iterates_to_no_positive_mdl_and_finds_stationarity():
    result = drive_recursive_port_hierarchy(
        0, _synthetic_callbacks(), maximum_levels=8)
    assert result.converged_no_positive_mdl
    assert result.termination_reason == "no_positive_mdl"
    assert len(result.levels) == 3
    assert result.levels[0].atom_supports == (12,)
    assert result.levels[0].admitted_macro_types == 1
    assert result.levels[0].quotient_macro_types == 1
    assert result.levels[1].atom_supports == (31,)
    assert result.levels[2].positive_macro_types == 0
    assert len(result.stationary_witnesses) == 1
    assert result.stationary_witnesses[0].lower_level == 0
    assert result.stationary_witnesses[0].upper_level == 1
    assert result.material_family_cell_scale_constants_unused


def test_normalization_removes_type_ids_node_order_and_uniform_scale():
    rotation = (1000, 0, 0, 0, 1000, 0, 0, 0, 1000)
    first = SimpleNamespace(
        node_types=(7, 9),
        edges=(MacroEdge(0, 1, (7, 9, rotation + (100, 0, 0))),),
        boundary_slots=(BoundarySlot(
            1, "outgoing", 11, (9, 11, rotation + (0, 200, 0)),
            2, 1.0),))
    second = SimpleNamespace(
        node_types=(3, 41),
        edges=(MacroEdge(1, 0, (41, 3, rotation + (250, 0, 0))),),
        boundary_slots=(BoundarySlot(
            0, "outgoing", 88, (3, 88, rotation + (0, 500, 0)),
            7, .25),))
    assert normalized_macro_signature(first) == normalized_macro_signature(second)


def test_real_macros_are_promoted_until_the_mdl_gate_closes():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    program = compile_irregular_port_program(nacl.species, nacl.positions)
    result = drive_recursive_port_hierarchy(
        program, real_first_level_callbacks())
    assert len(result.levels) >= 2
    assert result.levels[0].positive_macro_types > 0
    assert (result.levels[0].admitted_macro_types >=
            result.levels[0].quotient_macro_types)
    assert result.levels[0].total_mdl_saving > 0
    assert result.termination_reason == "no_positive_mdl"
    assert result.promotion_available
    assert result.converged_no_positive_mdl
    assert result.levels[-1].positive_macro_types == 0
    assert all(not level.certified_stationarity_signatures
               for level in result.levels)
    assert not result.stationary_witnesses


if __name__ == "__main__":
    test_injectable_driver_iterates_to_no_positive_mdl_and_finds_stationarity()
    test_normalization_removes_type_ids_node_order_and_uniform_scale()
    test_real_macros_are_promoted_until_the_mdl_gate_closes()
    print("recursive port hierarchy driver: passed")
