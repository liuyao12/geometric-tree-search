#!/usr/bin/env python3
"""Regression for target-free stage-local rollout execution."""

from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_frozen_stage_local_margin_marking import (
    load_default_model as load_prefix_model)
from materials_gcts_iqc_frozen_stage_local_rollout_value import (
    load_default_model as load_rollout_model)
from materials_gcts_iqc_obligation_expanded_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_stage_local_rollout_runtime import (
    execute_stage_local_rollout_search)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


def test_runtime_builds_frozen_eight_terminal_portfolio_without_target() -> None:
    group = 0
    seed, _ = oracle_crop_fast(DEVELOPMENT_CENTERS[group], SEED_RADIUS)
    result = execute_stage_local_rollout_search(
        load_default_runtime(), load_prefix_model(), load_rollout_model(),
        center=DEVELOPMENT_CENTERS[group], seed_positions=seed.positions,
        seed_species=seed.species, public_radius=TARGET_RADIUS)
    observed = tuple(row.action_key for row in result.candidates)
    assert len(observed) == 8
    assert len(set(observed)) == 8
    assert result.retained_counts_by_depth == (4, 8, 8)
    assert 0 <= result.selected_index < 8
    assert result.selected_state == result.candidates[result.selected_index].state
    assert len({round(row.rollout_score, 12) for row in result.candidates}) > 1
    assert len(result.candidate_digest) == 64
    assert not result.target_api_present
    assert not result.target_used


if __name__ == "__main__":
    test_runtime_builds_frozen_eight_terminal_portfolio_without_target()
    print("stage-local rollout runtime built target-free portfolio")
