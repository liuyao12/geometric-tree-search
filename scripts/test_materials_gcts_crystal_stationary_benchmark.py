#!/usr/bin/env python3
"""Focused contract tests for the generic crystal stationary benchmark."""

from __future__ import annotations

import random

from materials_gcts_crystal_stationary_benchmark import (
    _central_subset, _nacl_primitive_cube, certify_crystal_stationarity,
    evaluate)
from materials_gcts_generic import AtomicConfiguration


def _permuted(configuration: AtomicConfiguration) -> AtomicConfiguration:
    order = list(range(len(configuration.positions)))
    random.Random(713).shuffle(order)
    return AtomicConfiguration(
        configuration.name + "-permuted",
        tuple(configuration.positions[index] for index in order),
        tuple(configuration.species[index] for index in order))


def _simple_cubic(name: str, side: int, shift) -> AtomicConfiguration:
    positions = tuple((shift[0] + i, shift[1] + j, shift[2] + k)
                      for i in range(side) for j in range(side)
                      for k in range(side))
    return AtomicConfiguration(name, positions, ("A",) * len(positions))


def main() -> None:
    cases = evaluate()
    positive, iqc, amorphous = cases
    assert positive.accepted_generators
    assert len(positive.learned_generators) == 3
    assert all(value >= .45 for value in positive.generator_atomic_overlaps)
    assert tuple(item.side_in_base_cells for item in
                 positive.explicit_train_scales) == (2, 4, 8)
    assert all(item.exact and item.independent_occurrences >= 2
               for item in positive.explicit_train_scales)
    assert positive.heldout_first_two_levels_exact
    assert tuple(item.side_in_base_cells for item in
                 positive.heldout_explicit_scales) == (2, 4)
    assert all(item.exact and item.one_to_one_colored_match
               for item in positive.heldout_explicit_scales)
    assert tuple(item.materialized_sites for item in
                 positive.heldout_explicit_scales) == (16, 128)
    assert positive.production_children == 8
    assert positive.discovery_atoms == 216
    assert positive.training_sample_atoms == (1024, 1024)
    assert positive.learning_atom_presentations == 2264
    assert positive.unique_learning_atoms == 2048
    assert positive.discovery_is_subset_of_first_training_sample
    assert positive.stationary
    assert abs(positive.learned_similarity_scale - 2.0) < 1e-8
    assert positive.substitution_matrix == ((8,),)
    assert positive.base_sites == 2
    assert positive.symbolic_actions <= 7
    assert positive.represented_sites >= 1_000_000
    assert positive.million_sites_within_seven_actions
    assert not iqc.stationary and not iqc.million_sites_within_seven_actions
    assert not amorphous.stationary
    assert all(case.positions_species_and_learned_graph_only for case in cases)

    # Input ordering is not a hidden coordinate or construction-order channel.
    first = _nacl_primitive_cube("NaCl-order-A", 8, (0.0, 0.0, 0.0))
    second = _nacl_primitive_cube("NaCl-order-B", 8, (37.1, -11.0, 4.3))
    heldout = _nacl_primitive_cube("NaCl-order-H", 4, (-9.0, 5.0, 12.0))
    baseline = certify_crystal_stationarity(
        "baseline", _central_subset(first, 216), (first, second), heldout)
    shuffled_first = _permuted(first)
    shuffled = certify_crystal_stationarity(
        "shuffled", _central_subset(shuffled_first, 216),
        (shuffled_first, _permuted(second)), _permuted(heldout))
    assert baseline.stationary and shuffled.stationary
    rounded = lambda result: tuple(tuple(round(value, 9) for value in vector)
                                   for vector in result.learned_generators)
    assert rounded(baseline) == rounded(shuffled)
    assert baseline.substitution_matrix == shuffled.substitution_matrix

    # A ternary stationary grid is a counterexample to a hidden binary rule.
    # The learner must infer its radix, 27 child offsets, scale, and population
    # substitution through the same positions/species + occurrence-graph path.
    ternary_a = _simple_cubic("ternary-A", 27, (0.0, 0.0, 0.0))
    ternary_b = _simple_cubic("ternary-B", 27, (50.1, -2.2, 7.7))
    ternary_heldout = _simple_cubic("ternary-heldout", 9,
                                    (-20.3, 4.4, 8.8))
    ternary = certify_crystal_stationarity(
        "ternary", _central_subset(ternary_a, 64),
        (ternary_a, ternary_b), ternary_heldout)
    assert ternary.stationary
    assert ternary.learned_radix == 3
    assert ternary.production_children == 27
    assert tuple(item.side_in_base_cells for item in
                 ternary.explicit_train_scales) == (3, 9, 27)
    assert ternary.learned_similarity_scale == 3.0
    assert ternary.substitution_matrix == ((27,),)
    assert all(item.one_to_one_colored_match
               for item in ternary.heldout_explicit_scales)
    assert tuple(item.materialized_sites for item in
                 ternary.heldout_explicit_scales) == (27, 729)
    assert ternary.learning_atom_presentations == 39430
    assert ternary.unique_learning_atoms == 39366
    print("generic crystal stationary benchmark: all assertions passed")


if __name__ == "__main__":
    main()
