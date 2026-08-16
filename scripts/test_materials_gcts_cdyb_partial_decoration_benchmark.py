#!/usr/bin/env python3
"""Regression for disjoint published Cd--Yb partial decorations."""

from materials_gcts_cdyb_partial_decoration_benchmark import evaluate


def test_cdyb_partial_decoration_benchmark():
    result = evaluate()
    assert result.train_windows == 2
    assert result.train_atoms == 969
    assert result.eval_atoms == 478
    assert result.center_separation > 2 * 14
    assert result.raw_atom_ids_disjoint
    assert result.eval_atoms_geometry_covered == 449
    assert result.eval_geometry_atom_coverage > .93
    assert result.geometry_types > 0
    assert result.train_geometry_occurrences > 0
    assert result.complete_cover_with_gap_clusters
    assert result.residual_gap_atoms == \
        result.eval_atoms - result.eval_atoms_geometry_covered
    assert not result.target_labels_used_for_geometry_fit_or_factor_fit
    assert not result.source_sites_internal_coordinates_or_family_label_used
    assert result.modal_exact_accuracy == result.factor_exact_accuracy
    assert result.factor_site_accuracy > .94
    assert result.heldout_gap_marking_correct_atoms == 27
    assert not result.partial_section_gate_passed
    assert result.decoration_gate_passed == (
        result.factor_exact_accuracy >= .9 and
        result.factor_site_accuracy >= .99)
    assert result.partial_section_gate_passed == (
        result.decoration_gate_passed and
        result.heldout_gap_marking_accuracy >= .99)


if __name__ == "__main__":
    test_cdyb_partial_decoration_benchmark()
    print("CdYb partial decoration benchmark: assertions passed")
