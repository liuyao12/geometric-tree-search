#!/usr/bin/env python3

from materials_gcts_iqc_post_self_fed_fusion_value import (
    _representations, load_default_result)
from materials_gcts_iqc_self_fed_terminal_dataset import FEATURE_NAMES


def test_representation_indices_are_finite_unique_and_in_range():
    variants = _representations()
    assert tuple(row.name for row in variants) == (
        "incidence", "successor", "incidence+successor",
        "branch+successor")
    for row in variants:
        assert row.feature_indices
        assert len(set(row.feature_indices)) == len(row.feature_indices)
        assert min(row.feature_indices) >= 0
        assert max(row.feature_indices) < len(FEATURE_NAMES)


def test_frozen_nested_development_result_is_honestly_below_gate():
    row = load_default_result()
    assert row["supplied_groups"] == 9
    assert row["nested_selected_exact_groups"] == 7
    assert row["nested_selected_correct_sites"] == 26
    assert row["nested_top_band_all_exact_groups"] == 7
    assert not row["development_gate_passed"]
    assert row["minimum_selected_exact_supplied_groups"] == 8
    assert row["minimum_selected_correct_sites"] == 27
    assert row["final_selected_representation"] == "incidence"
    assert row["final_selected_neighbors"] == 1
    assert row["final_graph_rank_weight"] == .25
    assert row["unique_cached_graph_fits"] == 56
    assert not row["target_used_for_candidate_or_features"]
    assert not row["fresh_confirmation_claimed"]


if __name__ == "__main__":
    test_representation_indices_are_finite_unique_and_in_range()
    test_frozen_nested_development_result_is_honestly_below_gate()
    print("post-self-fed fusion-value tests passed")
