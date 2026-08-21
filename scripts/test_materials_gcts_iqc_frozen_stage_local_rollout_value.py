#!/usr/bin/env python3
"""Regression for the frozen stage-local rollout value model."""

from materials_gcts_iqc_frozen_stage_local_rollout_value import (
    EXPECTED_MODEL_DIGEST, fit_default_model, load_default_model,
    score_rollout)
from materials_gcts_iqc_stage_local_augmented_rollout_dataset import (
    load_default_dataset)


def test_frozen_rollout_model_reproduces_final_fit_and_scores_without_target() -> None:
    fitted = fit_default_model()
    frozen = load_default_model()
    assert frozen == fitted
    assert frozen.model_digest == EXPECTED_MODEL_DIGEST
    assert frozen.model_id == "temporal-61"
    assert frozen.family == "temporal"
    assert frozen.spec.neighbors == 7
    assert frozen.spec.horizon == 16
    assert frozen.spec.separation_channels
    assert len(frozen.training_rows) == 320
    assert len({row.group for row in frozen.training_rows}) == 20
    assert sum(row.exact for row in frozen.training_rows) > 0
    assert not frozen.target_used

    dataset = load_default_dataset()
    sample = tuple(row for group in dataset["groups"]
                   for row in group["rows"][:2])[:8]
    scores = tuple(score_rollout(
        frozen, row["transitions"], row["trace"]) for row in sample)
    assert len(scores) == 8
    assert all(0. <= score <= 1. for score in scores)
    assert len({round(score, 12) for score in scores}) > 2


if __name__ == "__main__":
    test_frozen_rollout_model_reproduces_final_fit_and_scores_without_target()
    print("frozen stage-local rollout value model passed")
