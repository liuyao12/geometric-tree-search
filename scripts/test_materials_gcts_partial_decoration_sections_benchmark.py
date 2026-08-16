#!/usr/bin/env python3
"""Regression for factorized cluster-decoration sections."""

from materials_gcts_partial_decoration_sections_benchmark import evaluate


def test_partial_decoration_sections_benchmark():
    result = evaluate()
    assert result.training_atoms == 4405
    assert result.heldout_atoms == 873
    assert result.train_occurrences > 0
    assert result.heldout_occurrences > 0
    assert result.train_unary_states > 0
    assert result.train_pair_states > result.train_unary_states
    assert result.heldout_factor_exact_accuracy > \
        result.heldout_modal_exact_accuracy
    assert result.heldout_factor_site_accuracy > \
        result.heldout_modal_site_accuracy
    assert result.heldout_factor_predictions_unseen_as_whole == 811
    assert result.heldout_unseen_whole_predictions_exact == 0
    assert not result.partial_section_gate_passed
    assert not result.target_species_used_for_fit_or_model_selection
    assert not result.family_phi_cell_or_potential_used
    assert result.partial_section_gate_passed == (
        result.heldout_factor_exact_accuracy >= .9 and
        result.heldout_factor_site_accuracy >= .99)


if __name__ == "__main__":
    test_partial_decoration_sections_benchmark()
    print("partial decoration sections benchmark: assertions passed")
