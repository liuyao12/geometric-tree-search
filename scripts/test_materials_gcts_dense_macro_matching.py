#!/usr/bin/env python3
"""Focused admission/deployment separation tests for dense macro matching."""

import math
import statistics

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import (
    execute_macro_derivation, score_macro_derivation)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros
from test_materials_gcts_port_graph_macros import _synthetic_program


def test_dense_matches_do_not_replace_sparse_mdl_evidence():
    program = _synthetic_program()
    mined = mine_port_graph_macros(
        program, maximum_nodes=3, geometry_tolerance=1e-6)
    dense = match_dense_macro_types(
        program, mined.macro_types, pose_tolerance=1e-6)
    assert dense.total_sparse_admission_occurrences == 10
    assert dense.total_dense_occurrences == 14
    assert dense.total_dense_occurrences > dense.total_sparse_admission_occurrences
    assert dense.every_dense_match_proper
    assert not dense.target_used
    assert not dense.family_cell_scale_used
    for original, deployed, audit in zip(
            mined.macro_types, dense.dense_macro_types, dense.audits):
        assert deployed.occurrences == original.occurrences
        assert deployed.mdl_saving == original.mdl_saving
        assert audit.admission_mdl_saving_unchanged
        assert len(deployed.promotion_occurrences) == audit.dense_occurrences
    promoted = promote_macro_types(
        program, dense.dense_macro_types, pose_tolerance=1e-6,
        minimum_shared_atoms=1)
    assert len(promoted.occurrences) == dense.total_dense_occurrences
    assert not promoted.target_used


def _nacl_dense_level():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    program = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(program, maximum_nodes=2)
    dense = match_dense_macro_types(program, mined.macro_types)
    promoted = promote_macro_types(program, dense.dense_macro_types)
    return nacl, mined, dense, promoted


def test_nacl_dense_promotion_reaches_the_frozen_frontier():
    nacl, mined, dense, promoted = _nacl_dense_level()
    assert len(mined.macro_types) == 3
    assert dense.total_sparse_admission_occurrences == 6
    assert dense.total_dense_occurrences == 246
    assert sum(audit.pose_fit_failures for audit in dense.audits) == 0
    assert len(promoted.occurrences) == 246
    assert promoted.atlas.ports and promoted.boundary_ports

    # Define an inner seed using training radii only.  Neither matching nor
    # replay receives the withheld outer atoms; they appear only in scoring.
    center = tuple(sum(point[axis] for point in nacl.positions) /
                   len(nacl.positions) for axis in range(3))
    radii = tuple(math.dist(point, center) for point in nacl.positions)
    cutoff = statistics.median(radii)
    inner = {index for index, radius in enumerate(radii) if radius <= cutoff}
    supports = dict(promoted.occurrence_supports)
    seeds = tuple(occurrence for occurrence in promoted.occurrences
                  if set(supports[occurrence.occurrence_id]) <= inner)
    seed_sites = tuple((nacl.species[index], nacl.positions[index])
                       for index in sorted(inner))
    derivation = execute_macro_derivation(
        promoted, seeds, explicit_seed_sites=seed_sites, maximum_levels=1,
        maximum_new_nodes_per_level=8)
    assert derivation.steps
    assert derivation.explicit_atom_count > len(seed_sites)
    assert not derivation.target_used
    score = score_macro_derivation(
        derivation, nacl.species, nacl.positions)
    assert not score.target_used_during_derivation
    assert score.correct_novel_atoms > 0


if __name__ == "__main__":
    test_dense_matches_do_not_replace_sparse_mdl_evidence()
    test_nacl_dense_promotion_reaches_the_frozen_frontier()
    print("dense frozen macro matching: passed")
