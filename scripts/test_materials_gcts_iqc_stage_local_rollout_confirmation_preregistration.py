#!/usr/bin/env python3
"""Contract test for the unopened stage-local rollout confirmation."""

from materials_gcts_iqc_stage_local_rollout_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST,
    REQUIRED_CENTER_SEPARATION, audit, select_confirmation_center)


def test_rollout_confirmation_is_fully_frozen_before_geometry() -> None:
    row = audit()
    assert row.manifest_digest == EXPECTED_MANIFEST_DIGEST
    assert row.source_hashes_verified
    assert row.center_selection_reproduced
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert row.minimum_consumed_center_separation > REQUIRED_CENTER_SEPARATION
    assert row.candidate_reach == (12, 4, 8)
    assert row.terminal_portfolio_budget == (4, 8, 8)
    assert row.self_fed_blocks == 3
    assert row.sites_per_block == 3
    assert not row.oracle_cropper_executor_scorer_imported
    assert not row.seed_target_candidates_scores_materialized
    assert not row.fresh_confirmation_claimed


if __name__ == "__main__":
    test_rollout_confirmation_is_fully_frozen_before_geometry()
    print("stage-local rollout confirmation preregistration passed")
