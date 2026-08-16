#!/usr/bin/env python3
"""Strict contracts for train-only Cd--Yb recurrent-core transfer."""

from materials_gcts_cdyb_recurrent_core_transfer_benchmark import evaluate


def test_predeclared_cdyb_recurrent_core_transfer_fails_closed_honestly():
    result = evaluate()
    assert result.training_patch_ids == (0, 1, 2, 3, 4)
    assert result.heldout_patch_ids == (5, 6)
    assert result.raw_domains_pairwise_disjoint
    assert result.majority_thresholds_by_level == (3,)
    assert result.raw_types_by_level == (80,)
    assert result.selected_types_by_level == (2,)
    assert result.training_complete_representation_by_level == (True,)
    assert result.selected_equals_transferred_by_level == (True,)
    assert result.transferred_occurrences_by_level == (4,)
    assert result.minimum_independent_occurrences_by_level == (2,)
    assert result.minimum_distinct_namespaces_by_level == (1,)
    assert result.certified_recursive_transfer_depth == 0
    assert result.complete_representation_by_level == (True,)
    assert result.exact_replay_by_level == (True,)
    assert result.frozen_ids_and_ports_preserved
    assert "fail-closed" in result.stopped_reason
    assert result.heldout_reencoding and not result.autonomous_growth
    assert not result.heldout_used_for_selection_or_refit


if __name__ == "__main__":
    test_predeclared_cdyb_recurrent_core_transfer_fails_closed_honestly()
    print("CdYb recurrent-core transfer benchmark passed")
