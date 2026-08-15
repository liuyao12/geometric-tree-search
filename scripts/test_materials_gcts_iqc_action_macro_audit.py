#!/usr/bin/env python3
"""Honest target-free IQC action-macro adapter gate."""

from materials_gcts_iqc_action_macro_audit import evaluate


def test_iqc_adapter_does_not_invent_three_wave_recurrence():
    result = evaluate(threshold_ratio=1.0, maximum_accepted_per_wave=16)
    assert (result.training_atoms, result.seed_atoms) == (887, 223)
    assert result.recognized_seed_occurrences == 20
    assert result.wave_candidate_counts == (309, 321, 367)
    assert result.wave_accepted_counts == (3, 1, 1)
    assert result.macro_child_counts == (3, 1, 1)
    assert result.exact_certified_action_macros == 3
    assert result.canonical_action_macros == 1
    assert result.recurring_three_wave_signatures == 0
    assert result.exact_cover_of_accepted_nodes
    assert not result.target_used


if __name__ == "__main__":
    test_iqc_adapter_does_not_invent_three_wave_recurrence()
    print("target-free IQC action-macro audit: passed")
