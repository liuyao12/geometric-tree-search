#!/usr/bin/env python3
"""Focused candidate-freezing and ranker-identity tests."""

import math

from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_exterior_candidate_executor import (
    enumerate_exterior_candidates, execute_exterior_wave)
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros


def test_rankers_receive_identical_frozen_candidate_ids():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, mined.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types)
    center = tuple(sum(point[axis] for point in nacl.positions) /
                   len(nacl.positions) for axis in range(3))
    radius = .7 * max(math.dist(point, center)
                      for point in nacl.positions)
    frozen = enumerate_exterior_candidates(
        promoted, promoted.occurrences,
        explicit_seed_sites=tuple(zip(nacl.species, nacl.positions)),
        boundary_origin=center, boundary_radius=radius)
    assert frozen.candidates
    assert not frozen.target_used
    assert len({item.candidate_id for item in frozen.candidates}) == len(
        frozen.candidates)
    default = execute_exterior_wave(frozen, maximum_candidates=8)
    evidence = execute_exterior_wave(
        frozen, maximum_candidates=8,
        ranker=lambda candidate: -sum(
            item.child_port_witnesses for item in candidate.evidence))
    assert default.candidate_ids == evidence.candidate_ids
    assert default.accepted_candidate_ids
    assert evidence.accepted_candidate_ids
    assert not default.target_used and not evidence.target_used


if __name__ == "__main__":
    test_rankers_receive_identical_frozen_candidate_ids()
    print("frozen exterior candidate executor: passed")
