#!/usr/bin/env python3
"""Brute-force parity for indexed incremental primitive frontier replay."""

import math

import materials_gcts_frozen_frontier_replay as replay_module
from materials_gcts_frozen_frontier_replay import (
    FrontierSeed, _classify_candidate, fit_frozen_frontier_program,
    replay_frontier)
from materials_gcts_generic import AtomicConfiguration
from materials_gcts_icosahedral_modelset import oracle_patch_fast
from materials_gcts_irregular_port_atlas import (
    compile_irregular_port_program, enumerate_frozen_port_occurrences)


class _BruteIndex:
    def __init__(self, sites, cell_size):
        self.sites = list(sites)

    def extend(self, sites):
        self.sites.extend(sites)

    def classify(self, sites, overlap_tolerance, exclusion_distance):
        return _classify_candidate(
            sites, self.sites, overlap_tolerance, exclusion_distance)


def _crop(configuration, center, radius):
    indices = tuple(index for index, point in enumerate(configuration.positions)
                    if math.dist(point, center) <= radius + 1e-10)
    return AtomicConfiguration(
        "crop", tuple(configuration.positions[index] for index in indices),
        tuple(configuration.species[index] for index in indices))


def test_indexed_replay_is_identical_to_brute_force_on_disjoint_iqc_seed():
    oracle, _ = oracle_patch_fast(8, 32.0)
    training = _crop(oracle, (-16.0, 0.0, 0.0), 11.0)
    seed_cloud = _crop(oracle, (8.0, 14.0, 7.0), 7.0)
    learned = compile_irregular_port_program(
        training.species, training.positions)
    frozen = fit_frozen_frontier_program(learned)
    enumeration = enumerate_frozen_port_occurrences(
        learned, seed_cloud.species, seed_cloud.positions,
        select_greedy_cover=True)
    covered = {index for _, support in enumeration.occurrence_supports
               for index in support}
    gaps = tuple((seed_cloud.species[index], seed_cloud.positions[index])
                 for index in range(len(seed_cloud.positions))
                 if index not in covered)
    seed = FrontierSeed(enumeration.occurrences, gaps)
    indexed = replay_frontier(frozen, seed, maximum_steps=10)
    original = replay_module._SpatialSiteIndex
    replay_module._SpatialSiteIndex = _BruteIndex
    try:
        brute = replay_frontier(frozen, seed, maximum_steps=10)
    finally:
        replay_module._SpatialSiteIndex = original
    assert indexed == brute


if __name__ == "__main__":
    test_indexed_replay_is_identical_to_brute_force_on_disjoint_iqc_seed()
    print("frozen frontier spatial parity: passed")
