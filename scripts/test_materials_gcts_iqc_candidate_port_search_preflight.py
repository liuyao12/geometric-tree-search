#!/usr/bin/env python3
"""Regression for individual two-step IQC carried-port search."""

from materials_gcts_iqc_candidate_port_search_preflight import evaluate


def test_candidate_port_search_keeps_reserved_nucleus_sealed():
    report = evaluate()
    assert report.reserved_confirmation_center_imported_or_accessed is False
    assert len(report.root_candidates_by_group) == 9
    assert min(report.root_positive_by_group) > 0
    assert min(report.positive_pairs_by_group) > 0
    assert report.selected_pairs == 9
    assert all(len(path) == 2 for path in report.selected_paths)
    assert report.connected_pairs_by_group == (
        2707, 1826, 1604, 1530, 1632, 1632, 1632, 1632, 1900)
    assert report.positive_pairs_by_group == (
        12, 53, 24, 14, 27, 27, 27, 27, 6)
    assert report.selected_correct_pairs == 5
    assert report.selected_false_pairs == 4
    assert report.preflight_passed == (
        report.selected_correct_pairs == 9 and
        report.selected_false_pairs == 0)


def main():
    test_candidate_port_search_keeps_reserved_nucleus_sealed()
    print("IQC candidate port search preflight test passed")


if __name__ == "__main__":
    main()
