#!/usr/bin/env python3
"""Exact parity tests for incremental replay collision indexing."""

import math
import random
import statistics

import materials_gcts_macro_derivation as derivation_module
from materials_gcts_dense_macro_matching import match_dense_macro_types
from materials_gcts_generic import benchmark_systems
from materials_gcts_irregular_port_atlas import compile_irregular_port_program
from materials_gcts_macro_derivation import (
    _SpatialSiteIndex, _classify, execute_macro_derivation)
from materials_gcts_macro_promotion import promote_macro_types
from materials_gcts_port_graph_macros import mine_port_graph_macros


class _BruteIndex:
    def __init__(self, sites, cell_size):
        self.sites = list(sites)

    def extend(self, sites):
        self.sites.extend(sites)

    def classify(self, rendered, tolerance, exclusion_distance):
        return _classify(
            rendered, self.sites, tolerance, exclusion_distance)


def test_spatial_classification_matches_brute_force_at_cell_boundaries():
    randomizer = random.Random(73019)
    tolerance = .03
    exclusion = .45
    occupied = (("A", (0.0, 0.0, 0.0)),) + tuple(
        (("A", "B")[index % 2],
         tuple(randomizer.uniform(-3.0, 3.0) for _ in range(3)))
        for index in range(80))
    index = _SpatialSiteIndex(occupied, exclusion)
    batches = []
    for _ in range(40):
        batch = tuple(
            (("A", "B")[site % 2],
             tuple(randomizer.uniform(-3.2, 3.2) for _ in range(3)))
            for site in range(9))
        batches.append(batch)
    # Explicitly exercise negative and positive cell faces and exact radii.
    batches.extend((
        (("A", (-.45, 0.0, 0.0)), ("B", (.45, 0.0, 0.0))),
        (("A", (tolerance, 0.0, 0.0)),),
        (("B", (tolerance, 0.0, 0.0)),),
    ))
    for batch in batches:
        assert index.classify(batch, tolerance, exclusion) == _classify(
            batch, occupied, tolerance, exclusion)


def _run_with_index(program, seeds, seed_sites, index_class):
    original = derivation_module._SpatialSiteIndex
    derivation_module._SpatialSiteIndex = index_class
    try:
        return execute_macro_derivation(
            program, seeds, explicit_seed_sites=seed_sites,
            maximum_levels=1, maximum_new_nodes_per_level=8)
    finally:
        derivation_module._SpatialSiteIndex = original


def test_nacl_replay_identity_and_order_match_brute_force():
    nacl = next(item for item in benchmark_systems()
                if item.name == "NaCl-rocksalt")
    atomic = compile_irregular_port_program(nacl.species, nacl.positions)
    mined = mine_port_graph_macros(atomic, maximum_nodes=2)
    dense = match_dense_macro_types(atomic, mined.macro_types)
    promoted = promote_macro_types(atomic, dense.dense_macro_types)
    center = tuple(sum(point[axis] for point in nacl.positions) /
                   len(nacl.positions) for axis in range(3))
    radii = tuple(math.dist(point, center) for point in nacl.positions)
    cutoff = statistics.median(radii)
    inner = {index for index, radius in enumerate(radii) if radius <= cutoff}
    supports = dict(promoted.occurrence_supports)
    seeds = tuple(occurrence for occurrence in promoted.occurrences
                  if set(supports[occurrence.occurrence_id]) <= inner)
    sites = tuple((nacl.species[index], nacl.positions[index])
                  for index in sorted(inner))
    brute = _run_with_index(promoted, seeds, sites, _BruteIndex)
    indexed = _run_with_index(promoted, seeds, sites, _SpatialSiteIndex)
    assert indexed == brute


if __name__ == "__main__":
    test_spatial_classification_matches_brute_force_at_cell_boundaries()
    test_nacl_replay_identity_and_order_match_brute_force()
    print("macro derivation spatial-index parity: passed")
