#!/usr/bin/env python3
from types import SimpleNamespace

from materials_gcts_iqc_held_forward_beam_benchmark import audit


def decision(wave, rank, true, false, rollback=0, target=False):
    return SimpleNamespace(
        wave=wave, selected_rank=rank, selected_true_sites=true,
        selected_false_sites=false, greedy_rollback=rollback,
        target_used_for_selection=target)


def test_three_clean_future_decisions_pass_without_overclaiming():
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0, 1),
        decision(18, 1, 24, 0),
        decision(19, 2, 36, 0, 1),
        decision(20, 1, 12, 0),
    )))
    assert result.temporal_confirmation_passed
    assert result.held_forward_true_sites == 72
    assert result.held_forward_false_sites == 0
    assert result.held_forward_rollbacks == 1
    assert not result.selection_uses_truth
    assert not result.target_used_for_selection
    assert not result.spatially_independent_confirmation
    assert not result.stationary_or_exponential_certificate


def test_wrong_or_target_conditioned_future_decision_fails():
    wrong = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0), decision(18, 1, 11, 1),
        decision(19, 1, 12, 0), decision(20, 1, 12, 0))))
    leaked = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0), decision(18, 1, 12, 0, target=True),
        decision(19, 1, 12, 0), decision(20, 1, 12, 0))))
    assert not wrong.temporal_confirmation_passed
    assert not leaked.temporal_confirmation_passed
    assert leaked.target_used_for_selection


def test_real_wave17_policy_fails_on_the_held_forward_suffix():
    # Frozen result of the target-free width-two execution.  Wave 17 is the
    # exploratory success; waves 18--24 are never allowed to tune the policy.
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0, 1),
        decision(18, 2, 0, 12, 1),
        decision(19, 2, 0, 24, 1),
        decision(20, 1, 0, 24),
        decision(21, 2, 24, 0, 1),
        decision(22, 2, 12, 0, 1),
        decision(23, 1, 0, 12),
        decision(24, 2, 4, 0, 1),
    )))
    assert result.held_forward_decision_waves == tuple(range(18, 25))
    assert result.held_forward_true_sites == 40
    assert result.held_forward_false_sites == 72
    assert result.held_forward_rollbacks == 5
    assert not result.temporal_confirmation_passed


if __name__ == "__main__":
    test_three_clean_future_decisions_pass_without_overclaiming()
    test_wrong_or_target_conditioned_future_decision_fails()
    test_real_wave17_policy_fails_on_the_held_forward_suffix()
    print("held-forward IQC beam benchmark tests: passed")
