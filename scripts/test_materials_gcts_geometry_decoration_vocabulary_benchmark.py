#!/usr/bin/env python3
"""Regression for geometry-first decoration vocabulary transfer."""

from materials_gcts_geometry_decoration_vocabulary_benchmark import evaluate


def test_geometry_decoration_vocabulary():
    result = evaluate()
    assert result.training_atoms == 4405
    assert result.heldout_atoms == 873
    assert result.geometry_types > 0
    assert result.train_geometry_occurrences > 0
    assert len(result.frozen_vocabulary_digest) == 64
    assert result.geometry_fit_before_target_opened
    assert not result.heldout_used_for_geometry_or_decoration_fit
    assert not result.family_phi_cell_or_potential_used
    assert result.heldout_atoms_geometry_covered <= result.heldout_atoms
    assert result.heldout_atoms_known_decoration_covered <= \
        result.heldout_atoms_geometry_covered
    assert result.representation_gate_passed == (
        result.heldout_geometry_atom_coverage == 1. and
        result.heldout_known_decoration_atom_coverage >= .95 and
        result.heldout_decoration_occurrence_coverage >= .9 and
        result.geometry_types_with_multiple_decorations > 0)


if __name__ == "__main__":
    test_geometry_decoration_vocabulary()
    print("geometry-decoration vocabulary benchmark: assertions passed")
