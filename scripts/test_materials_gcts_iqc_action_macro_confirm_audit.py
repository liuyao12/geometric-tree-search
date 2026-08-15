#!/usr/bin/env python3
"""Exact five-wave confirmatory action-macro audit."""

from materials_gcts_iqc_action_macro_audit import evaluate


def test_confirmatory_multiwave_macros_are_exact_but_not_stationary():
    result = evaluate(
        threshold_ratio=15 / 21,
        maximum_accepted_per_wave=40,
        maximum_waves=5,
        training_center=(-16.0, 0.0, 0.0),
        seed_center=(5.0, -17.0, 4.0),
        training_radius=11.0,
        seed_radius=7.0,
        public_boundary_radius=11.0)
    assert (result.training_atoms, result.seed_atoms) == (887, 231)
    assert result.recognized_seed_occurrences == 25
    assert result.wave_candidate_counts == (274, 276, 316, 314, 312)
    assert result.wave_maximum_minimum_support == (17, 14, 15, 11, 14)
    assert result.wave_accepted_counts == (3, 17, 4, 30, 5)
    assert result.emitted_atoms == 109
    assert result.macro_child_counts == (3, 17, 3, 1, 26, 4, 4, 1)
    assert result.macro_waves == (1, 2, 3, 3, 4, 4, 5, 5)
    assert result.action_macros == result.exact_certified_action_macros == 8
    assert result.canonical_action_macros == 6
    assert all(len(waves) == 1
               for _, waves in result.normalized_key_wave_support)
    assert result.recurring_three_wave_signatures == 0
    assert not result.hierarchy_stationarity_claimed
    assert result.exact_cover_of_accepted_nodes
    assert result.executor_result_digest == (
        "ad6d9d04c621c940defb33d6919acb88"
        "e6c563a15c428d0483494b501d297720")
    assert not result.target_used


if __name__ == "__main__":
    test_confirmatory_multiwave_macros_are_exact_but_not_stationary()
    print("confirmatory five-wave action-macro audit: passed")
