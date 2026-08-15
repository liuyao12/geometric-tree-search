#!/usr/bin/env python3

from dataclasses import replace

from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import execute_macro_derivation
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from test_materials_gcts_port_graph_macros import _synthetic_program


def test_synthetic_self_fed_derivation_has_inclusion_certificates():
    atomic = _synthetic_program()
    macros = mine_port_graph_macros(
        atomic, maximum_nodes=3, geometry_tolerance=1e-6)
    level = promote_macro_types(
        atomic, macros.macro_types, pose_tolerance=1e-6,
        minimum_shared_atoms=1)
    result = execute_macro_derivation(
        level, level.occurrences[:1], maximum_levels=2,
        pose_tolerance=1e-6)
    assert len(result.steps) == 2
    assert result.explicit_levels[0].emitted_nodes == 2
    assert result.explicit_levels[0].atoms_before == 7
    assert result.explicit_levels[0].emitted_atoms == 6
    assert result.explicit_levels[0].atoms_after == 13
    assert result.explicit_levels[1].parent_nodes == 2
    assert all(step.certificate.overlap_is_subset and
               step.certificate.emitted_is_exact_difference and
               step.certificate.adjacency_witnessed_in_training and
               len(step.certificate.included_overlap_sites) >=
               step.certificate.required_shared_atoms
               for step in result.steps)
    assert len({step.certificate.certificate_digest
                for step in result.steps}) == len(result.steps)
    assert result.independent_count_verified
    assert result.symbolic_atom_count == result.explicit_atom_count == 13
    assert result.self_fed and not result.target_used
    assert result.stationary_contract is not None
    assert result.stationary_normalized_key

    # Collision exclusion comes from the learned minimum distance, not an
    # arbitrary multiple of pose tolerance. A geometrically distinct blocker
    # inside 0.45*d_min removes at least one otherwise valid child.
    emitted = next(site for site in result.sites
                   if site not in result.seed_sites)
    blocked_level = replace(level, minimum_distance=1.0)
    blocker = (("blocker", (emitted[1][0], emitted[1][1] + .2,
                            emitted[1][2])),)
    blocked = execute_macro_derivation(
        blocked_level, blocked_level.occurrences[:1],
        explicit_seed_sites=blocker, maximum_levels=1,
        pose_tolerance=.01)
    assert blocked.rejected_conflicts > 0
    assert len(blocked.steps) < len(result.steps)


def test_nacl_promoted_overlap_is_honestly_not_yet_a_growth_rule():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    macros = mine_port_graph_macros(atomic, maximum_nodes=2)
    level = promote_macro_types(atomic, macros.macro_types)
    result = execute_macro_derivation(
        level, level.occurrences[:1], maximum_levels=2)
    assert result.productions
    assert result.attempted_candidates > 0
    assert result.rejected_duplicate_poses > 0
    assert not result.steps
    assert result.explicit_levels[0].emitted_nodes == 0
    assert result.independent_count_verified
    assert result.symbolic_atom_count == result.explicit_atom_count
    assert not result.stationary_normalized_key
    full_seed = execute_macro_derivation(
        level, level.occurrences,
        explicit_seed_sites=tuple(zip(nacl.species, nacl.positions)),
        maximum_levels=1)
    assert len(full_seed.seed_sites) == len(nacl.positions)
    assert full_seed.explicit_atom_count == len(nacl.positions)


if __name__ == "__main__":
    test_synthetic_self_fed_derivation_has_inclusion_certificates()
    test_nacl_promoted_overlap_is_honestly_not_yet_a_growth_rule()
    print("self-fed certified macro derivation: passed")
