#!/usr/bin/env python3

from materials_gcts_iqc_multinucleus_marking_benchmark import evaluate


def test_multinucleus_marker_places_exact_option_inside_beam_but_value_fails():
    report = evaluate(1)
    assert report.all_target_balls_pairwise_disjoint
    assert report.training_seed_atoms == (507, 482, 472)
    assert report.training_target_atoms == (1969, 2039, 2044)
    assert report.training_examples == 15830
    assert report.training_positives == 3171
    assert report.confirmation_seed_atoms == 484
    assert report.confirmation_target_atoms == 2025
    assert report.frozen_candidates == 5422
    assert report.candidate_true_sites == (0, 0, 0, 2)
    assert report.candidate_false_sites == (1, 3, 2, 0)
    assert report.selected_ranks == (2,)
    assert report.correct_sites == 0
    assert report.false_sites == 3
    assert report.raw_execution_truth_fields_unavailable
    assert not report.target_used_for_selection
    assert not report.spatial_confirmation_passed


if __name__ == "__main__":
    test_multinucleus_marker_places_exact_option_inside_beam_but_value_fails()
    print("multi-nucleus IQC marking benchmark tests: passed")
