#!/usr/bin/env python3

from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_oriented_overlap_ports import is_proper_rotation
from materials_gcts_port_graph_macros import mine_port_graph_macros
from materials_gcts_sparse_occurrence_graph import reduce_occurrence_graph
from test_materials_gcts_port_graph_macros import _synthetic_program


def _assert_promoted_contract(level):
    assert level.prototypes
    assert len(level.occurrences) >= 2
    assert len(level.occurrence_supports) == len(level.occurrences)
    assert all(is_proper_rotation(item.rotation)
               for item in level.occurrences)
    assert not level.family_label_used
    assert not level.lattice_used
    assert not level.physical_potential_used
    assert not level.target_used
    assert level.conflicting_atom_unions == 0
    assert level.minimum_distance > 0


def test_synthetic_macros_promote_and_run_the_generic_pipeline_again():
    atomic = _synthetic_program()
    mined = mine_port_graph_macros(
        atomic, maximum_nodes=3, geometry_tolerance=1e-6)
    level = promote_macro_types(
        atomic, mined.macro_types, pose_tolerance=1e-6,
        minimum_shared_atoms=1)
    _assert_promoted_contract(level)
    assert level.atlas.ports
    assert level.boundary_ports
    assert level.boundary_relation_classes
    assert all(len(prototype.sites) > 4 for prototype in level.prototypes)
    reduced = reduce_occurrence_graph(level)
    assert reduced.source_nodes == len(level.occurrences)
    assert reduced.complete_repeated_support_cover
    second = mine_port_graph_macros(
        level, maximum_nodes=2, geometry_tolerance=1e-6)
    assert second.source_graph_vertices == len(level.occurrences)


def test_nacl_macros_become_proper_next_level_nodes():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    level = promote_macro_types(atomic, mined.macro_types)
    _assert_promoted_contract(level)
    assert len(level.prototypes) == len(mined.macro_types)
    assert len(level.occurrences) == sum(
        len(macro.occurrences) for macro in mined.macro_types)
    assert level.atlas.ports
    assert level.boundary_ports
    assert all(port.occurrence_observations >= 2
               for port in level.boundary_ports)
    reduced = reduce_occurrence_graph(level)
    assert reduced.source_nodes == len(level.occurrences)
    # The public next-level program can be handed straight back to the miner;
    # whether another positive-MDL macro exists is evidence, not assumed.
    second = mine_port_graph_macros(level, maximum_nodes=2)
    assert second.source_graph_vertices == len(level.occurrences)


if __name__ == "__main__":
    test_synthetic_macros_promote_and_run_the_generic_pipeline_again()
    test_nacl_macros_become_proper_next_level_nodes()
    print("generic MacroType-as-node promotion: passed")
