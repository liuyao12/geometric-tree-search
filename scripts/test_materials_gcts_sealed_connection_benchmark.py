#!/usr/bin/env python3

from materials_gcts_sealed_connection_benchmark import evaluate


def test_seed_only_connection_gate_is_honestly_red() -> None:
    result = evaluate()
    assert result.training_atoms == 507
    assert result.training_inner_parents == 93
    assert result.evaluation_state_atoms == 1969
    assert result.heldout_novel_atoms == 6634
    assert result.scale_error < 1e-12
    assert result.training_targets_within_seed_only
    assert not result.evaluation_windows_used_for_learning
    assert not result.physical_potential_used
    assert result.novel_proposals == 3404
    assert result.true_novel_proposals == 500
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_seed_only_connection_gate_is_honestly_red()
    print("sealed seed-only connection benchmark: honest red gate passed")
