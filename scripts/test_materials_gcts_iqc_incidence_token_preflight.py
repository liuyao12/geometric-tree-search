#!/usr/bin/env python3
"""Exact regression for the nine-nucleus candidate-incidence preflight."""

from materials_gcts_iqc_incidence_token_preflight import evaluate


def test_candidate_incidence_preflight_is_honestly_gated():
    report = evaluate()
    assert report.reserved_confirmation_center_imported_or_accessed is False
    assert report.total_candidates == 44602
    assert report.positive_candidates == 3689
    assert report.threshold_precision >= .95
    assert report.antichain_precision >= .95
    assert report.antichain_correct_candidates == 25
    assert report.antichain_false_candidates == 1
    assert report.antichain_selected_candidates < 18 or \
        report.exact_groups < 9
    assert report.preflight_passed is False


def main():
    test_candidate_incidence_preflight_is_honestly_gated()
    print("IQC candidate incidence preflight test passed")


if __name__ == "__main__":
    main()
