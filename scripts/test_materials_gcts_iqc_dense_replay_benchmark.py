#!/usr/bin/env python3
"""Slow reproducibility gate for the dense IQC central-seed claim."""

from materials_gcts_iqc_dense_replay_benchmark import evaluate


def test_iqc_dense_central_seed_replay_is_target_blind_and_exact():
    result = evaluate()
    assert result.training_atoms == 507
    assert result.dense_promotion_occurrences == 2520
    assert result.seed_atoms == 30
    assert result.accepted_nodes == 16
    assert result.emitted_atoms == 86
    assert result.correct_emitted_atoms == 86
    assert result.precision == 1.0
    assert result.training_reconstruction_recall > .18
    assert result.evaluation_geometry_seen_during_learning
    assert not result.target_used_during_replay


if __name__ == "__main__":
    test_iqc_dense_central_seed_replay_is_target_blind_and_exact()
    print("slow dense IQC replay benchmark: passed")
