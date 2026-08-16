#!/usr/bin/env python3
"""Regression for overlap-constrained decoration reconstruction."""

from materials_gcts_decoration_cover_solver_benchmark import evaluate


def test_decoration_cover_solver():
    result = evaluate()
    assert result.training_atoms == 4405
    assert result.evaluation_atoms == 873
    assert result.seed_atoms_with_known_species == 226
    assert result.outer_atoms_species_hidden_from_solver == 647
    assert result.geometry_types > 0
    assert result.train_decoration_alternatives > result.geometry_types
    assert result.frozen_candidate_occurrences > 0
    assert result.initial_decoration_states >= \
        result.seed_inconsistent_states_removed
    assert result.propagation_rounds >= 1
    assert not result.outer_species_used_by_solver
    assert result.target_positions_used_for_reencoding
    assert not result.autonomous_growth_claimed
    assert result.benchmark_passed == (
        result.inferred_precision >= .99 and
        result.inferred_outer_recall >= .9)


if __name__ == "__main__":
    test_decoration_cover_solver()
    print("decoration cover solver benchmark: assertions passed")
