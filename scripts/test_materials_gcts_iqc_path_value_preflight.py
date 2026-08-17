#!/usr/bin/env python3
"""Regression for target-free third-frontier IQC path valuation."""

from materials_gcts_iqc_path_value_preflight import evaluate


def test_path_value_preflight_has_exact_supply_and_sealed_target():
    report = evaluate()
    assert report.reserved_confirmation_center_imported_or_accessed is False
    assert report.shortlist_candidates_by_group == (512,) * 9
    assert min(report.shortlist_positive_by_group) > 0
    assert len(report.selected_path_ids) == 9
    assert report.shortlist_positive_by_group == (
        12, 22, 15, 10, 13, 13, 13, 13, 2)
    assert report.selected_correct_paths == 4
    assert report.selected_false_paths == 5
    assert report.preflight_passed == (
        report.selected_correct_paths == 9 and
        report.selected_false_paths == 0)


def main():
    test_path_value_preflight_has_exact_supply_and_sealed_target()
    print("IQC path value preflight test passed")


if __name__ == "__main__":
    main()
