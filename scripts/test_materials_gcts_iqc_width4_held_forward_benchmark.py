#!/usr/bin/env python3
from types import SimpleNamespace

from materials_gcts_iqc_width4_held_forward_benchmark import audit


def decision(wave, rank, true, false, rollback=0, target=False):
    return SimpleNamespace(
        wave=wave, selected_rank=rank, selected_true_sites=true,
        selected_false_sites=false, greedy_rollback=rollback,
        target_used_for_selection=target)


def test_clean_later_states_pass_without_exponential_overclaim():
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0, 1), decision(18, 4, 12, 0, 1),
        decision(19, 3, 24, 0, 1), decision(20, 1, 12, 0),
        decision(21, 2, 24, 0, 1))))
    assert result.exploratory_selected_ranks == (2, 4)
    assert result.held_forward_true_sites == 60
    assert result.held_forward_false_sites == 0
    assert result.temporal_gate_passed
    assert not result.spatially_independent_confirmation
    assert not result.stationary_or_exponential_certificate


def test_later_error_or_target_use_fails():
    wrong = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0), decision(18, 4, 12, 0),
        decision(19, 1, 12, 1), decision(20, 1, 12, 0),
        decision(21, 1, 12, 0))))
    leaked = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0), decision(18, 4, 12, 0),
        decision(19, 1, 12, 0, target=True), decision(20, 1, 12, 0),
        decision(21, 1, 12, 0))))
    assert wrong.first_failure_wave == 19
    assert not wrong.temporal_gate_passed
    assert leaked.target_used_for_selection
    assert not leaked.temporal_gate_passed


def test_real_width_four_trace_is_an_honest_red_result():
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0, 1), decision(18, 4, 12, 0, 1),
        decision(19, 1, 0, 24), decision(20, 3, 0, 24, 1),
        decision(21, 1, 12, 0), decision(22, 4, 24, 0, 1),
        decision(23, 4, 0, 12, 1), decision(24, 4, 0, 8, 1),
    )))
    assert result.held_forward_true_sites == 36
    assert result.held_forward_false_sites == 68
    assert result.first_failure_wave == 19
    assert result.held_forward_rollbacks == 4
    assert not result.temporal_gate_passed


if __name__ == "__main__":
    test_clean_later_states_pass_without_exponential_overclaim()
    test_later_error_or_target_use_fails()
    test_real_width_four_trace_is_an_honest_red_result()
    print("width-four IQC held-forward benchmark tests: passed")
