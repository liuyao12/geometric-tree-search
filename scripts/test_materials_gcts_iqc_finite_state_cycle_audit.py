#!/usr/bin/env python3
"""Slow current-IQC negative gate for finite-state recurrence."""

from materials_gcts_iqc_finite_state_cycle_audit import evaluate


def test_current_iqc_hierarchy_is_honestly_red_for_cycle_recurrence():
    result = evaluate()
    assert result.positive_train_levels == 4
    assert result.minimum_levels_for_two_state_two_traversal_cycle == 5
    assert not result.enough_levels_to_learn_nontrivial_cycle
    assert not result.heldout_scale_independently_observed
    assert not result.finite_state_cycle_recurrence
    assert not result.stationary_gate_weakened
    assert result.heldout_reencoding
    assert not result.autonomous_growth
    assert not result.target_used_to_select_cycle
    assert result.shuffled_transition_control_pass_required
    assert result.chemistry_population_port_control_pass_required


if __name__ == "__main__":
    test_current_iqc_hierarchy_is_honestly_red_for_cycle_recurrence()
    print("current IQC finite-state cycle audit: all assertions passed")
