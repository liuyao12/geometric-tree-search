#!/usr/bin/env python3
"""Focused execution test for the frozen stage-local IQC marking."""

import inspect

from materials_gcts_iqc_frozen_fusion_runtime import load_default_runtime
from materials_gcts_iqc_frozen_stage_local_prefix_marking import (
    EXPECTED_MODEL_DIGEST, load_default_model)
from materials_gcts_iqc_obligation_expanded_dataset import _site_key
from materials_gcts_iqc_obligation_expanded_preregistration import (
    DEVELOPMENT_CENTERS, SEED_RADIUS, TARGET_RADIUS)
from materials_gcts_iqc_stage_local_prefix_runtime import (
    execute_stage_local_prefix_search)
from materials_gcts_icosahedral_modelset import oracle_crop_fast


def test_frozen_stage_local_search_retains_an_exact_consumed_prefix():
    assert "target" not in inspect.signature(
        execute_stage_local_prefix_search).parameters
    model = load_default_model()
    assert model.model_digest == EXPECTED_MODEL_DIGEST
    assert model.candidate_reach == (12, 4, 8)
    assert model.retained_prefix_budget == (2, 4, 1)
    assert tuple(row.spec.variant for row in model.depth_models) == (
        "branch", "section", "branch")
    assert model.training_target_labels_used
    assert not model.fresh_confirmation_target_used
    assert not model.candidate_geometry_authorized

    center = DEVELOPMENT_CENTERS[0]
    seed, _ = oracle_crop_fast(center, SEED_RADIUS)
    result = execute_stage_local_prefix_search(
        load_default_runtime(), model, center=center,
        seed_positions=seed.positions, seed_species=seed.species,
        public_radius=TARGET_RADIUS)
    assert result.candidate_counts_by_depth == (12, 8, 29)
    assert result.retained_counts_by_depth == (2, 4, 1)
    assert result.geometry_digest == \
        "c71c07ca98e06dda461327f0c8399487f1977c177cb54cbf96aaac105073fa0f"
    assert len(result.final_states) == 1
    assert not result.target_api_present
    assert not result.target_used

    # The consumed target is constructed only after the target-free result.
    target, _ = oracle_crop_fast(center, TARGET_RADIUS)
    truth = {_site_key(point): str(color) for point, color in zip(
        target.positions, target.species)}
    assert all(truth.get(_site_key(point)) == str(color)
               for point, color in result.final_states[0].actions)


if __name__ == "__main__":
    test_frozen_stage_local_search_retains_an_exact_consumed_prefix()
    print("frozen stage-local IQC runtime regression passed")
