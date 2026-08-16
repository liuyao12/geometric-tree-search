#!/usr/bin/env python3
"""Regression for published Cd--Yb decoration tree search."""

from materials_gcts_cdyb_decoration_tree_search_benchmark import evaluate


def test_cdyb_decoration_tree_search_benchmark():
    result = evaluate(shuffle_trials=31)
    assert result.train_atoms == 969
    assert result.eval_atoms == 478
    assert result.raw_atom_ids_disjoint
    assert result.seed_atoms > 0
    assert result.frozen_decoration_actions > 0
    assert result.identical_candidate_digest_all_arms
    assert result.gcts.correct_outer_atoms == 378
    assert result.gcts.wrong_outer_atoms == 0
    assert result.gcts.recall > .9
    assert result.modal.correct_outer_atoms == 377
    assert result.gcts_correct_atoms_empirical_p == .03125
    assert result.gcts_beats_shuffles
    assert result.reconstruction_gate_passed
    assert not result.target_labels_used_during_compile_or_search
    assert not result.source_sites_internal_coordinates_or_family_label_used
    assert not result.autonomous_growth_claimed
    assert result.reconstruction_gate_passed == (
        result.gcts.precision >= .99 and result.gcts.recall >= .9 and
        result.gcts_beats_shuffles)


if __name__ == "__main__":
    test_cdyb_decoration_tree_search_benchmark()
    print("CdYb decoration tree search benchmark: assertions passed")
