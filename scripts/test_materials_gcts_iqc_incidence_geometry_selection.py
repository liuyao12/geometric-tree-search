#!/usr/bin/env python3
"""Regression for nested, train-only IQC marking-geometry selection."""

from materials_gcts_iqc_incidence_geometry_selection import evaluate


def test_nested_geometry_selection_keeps_confirmation_sealed():
    report = evaluate()
    assert report.reserved_confirmation_center_imported_or_accessed is False
    assert report.candidate_graph_digest == \
        "69ec0af6c6c67fc12e2c26b9701095b9199f2f36a877536ecc8cecb9afc629b6"
    assert report.candidates_by_group == (
        4164, 5156, 5008, 4842, 5034, 5034, 5034, 5034, 5296)
    assert report.selected_by_group == (20, 4, 5, 6, 3, 9, 9, 5, 4)
    assert report.correct_by_group == (0, 4, 3, 6, 3, 9, 9, 5, 2)
    assert report.selected_candidates == 65
    assert report.correct_candidates == 41
    assert report.exact_groups == 6
    assert report.minimum_selected_per_group == 3
    assert report.rank_two_correct_by_group == (0, 2, 2, 2, 2, 2, 2, 2, 2)
    assert report.rank_two_correct_candidates == 16
    assert report.rank_two_precision == 16 / 18
    assert report.nested_gate_passed is False


def main():
    test_nested_geometry_selection_keeps_confirmation_sealed()
    print("IQC nested incidence-geometry selection test passed")


if __name__ == "__main__":
    main()
