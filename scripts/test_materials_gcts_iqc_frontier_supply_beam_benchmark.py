#!/usr/bin/env python3
from types import SimpleNamespace

from materials_gcts_iqc_frontier_supply_beam_benchmark import audit


def decision(wave, rank, true, false, rollback=0, target=False):
    return SimpleNamespace(
        wave=wave, selection_objective="frontier-supply",
        selected_rank=rank, selected_true_sites=true,
        selected_false_sites=false, greedy_rollback=rollback,
        target_used_for_selection=target)


def test_clean_future_passes_as_temporal_evidence_only():
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0, 1), decision(18, 4, 12, 0, 1),
        decision(19, 4, 24, 0, 1), decision(20, 3, 12, 0, 1),
        decision(21, 1, 24, 0), decision(22, 2, 12, 0, 1))))
    assert result.exploratory_selected_ranks == (2, 4, 4)
    assert result.held_forward_true_sites == 48
    assert result.held_forward_false_sites == 0
    assert result.temporal_gate_passed
    assert not result.spatially_independent_confirmation
    assert not result.stationary_or_exponential_certificate


def test_wrong_future_fails():
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0), decision(18, 4, 12, 0),
        decision(19, 4, 24, 0), decision(20, 1, 0, 12),
        decision(21, 1, 12, 0), decision(22, 1, 12, 0))))
    assert result.first_failure_wave == 20
    assert not result.temporal_gate_passed


def test_real_option_preserving_trace_passes_held_forward_gate():
    result = audit(SimpleNamespace(regenerative_beam_decisions=(
        decision(17, 2, 48, 0, 1), decision(18, 4, 12, 0, 1),
        decision(19, 4, 24, 0, 1), decision(20, 2, 24, 0, 1),
        decision(21, 3, 24, 0, 1), decision(22, 1, 24, 0),
        decision(23, 4, 24, 0, 1), decision(24, 4, 24, 0, 1),
    )))
    assert result.exploratory_true_sites == 84
    assert result.exploratory_false_sites == 0
    assert result.held_forward_selected_ranks == (2, 3, 1, 4, 4)
    assert result.held_forward_true_sites == 120
    assert result.held_forward_false_sites == 0
    assert result.held_forward_rollbacks == 4
    assert result.first_failure_wave is None
    assert result.temporal_gate_passed


if __name__ == "__main__":
    test_clean_future_passes_as_temporal_evidence_only()
    test_wrong_future_fails()
    test_real_option_preserving_trace_passes_held_forward_gate()
    print("frontier-supply IQC beam benchmark tests: passed")
