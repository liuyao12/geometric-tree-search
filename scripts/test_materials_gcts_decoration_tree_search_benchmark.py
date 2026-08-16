#!/usr/bin/env python3
"""Regression for sealed optional-decoration tree search."""

from materials_gcts_decoration_tree_search_benchmark import evaluate


def test_decoration_tree_search_benchmark():
    result = evaluate(shuffle_trials=2,
                      minimum_marking_probability=.99,
                      minimum_overlap_atoms=6)
    assert result.training_atoms == 4405
    assert result.evaluation_atoms == 873
    assert result.seed_atoms == 226
    assert result.frozen_decoration_actions > result.frozen_geometry_occurrences
    assert len(result.candidate_digest) == 64
    assert result.identical_candidate_digest_all_arms
    assert result.gcts.correct_outer_atoms == 354
    assert result.gcts.wrong_outer_atoms == 61
    assert result.modal.correct_outer_atoms == 116
    assert result.target_positions_supplied_for_reconstruction
    assert not result.outer_species_used_during_search
    assert not result.target_used_by_search_api
    assert not result.autonomous_growth_claimed
    assert result.reconstruction_gate_passed == (
        result.gcts.precision >= .99 and result.gcts.recall >= .9 and
        result.gcts_beats_shuffles)


if __name__ == "__main__":
    test_decoration_tree_search_benchmark()
    print("decoration tree-search benchmark: assertions passed")
