#!/usr/bin/env python3

from materials_gcts_large_production_replay_benchmark import evaluate


def test_large_production_recognition_does_not_fake_execution() -> None:
    result = evaluate(1024)
    assert result.training_atoms == 28211
    assert result.heldout_atoms == 155097
    assert not result.heldout_geometry_used_for_fitting
    assert not result.production_execution_verified
    assert not result.benchmark_passed


if __name__ == "__main__":
    test_large_production_recognition_does_not_fake_execution()
    print("large frozen production replay: honest execution gate passed")
