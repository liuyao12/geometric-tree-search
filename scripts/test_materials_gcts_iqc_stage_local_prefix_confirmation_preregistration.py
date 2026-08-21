#!/usr/bin/env python3
"""Fast contract test for the fresh stage-local IQC confirmation manifest."""

from materials_gcts_iqc_stage_local_prefix_confirmation_preregistration import (
    EXPECTED_MANIFEST_DIGEST, REQUIRED_CENTER_SEPARATION, audit)


def test_stage_local_confirmation_is_frozen_before_atom_access():
    row = audit()
    assert row.manifest_digest == EXPECTED_MANIFEST_DIGEST
    assert row.source_hashes_verified
    assert row.center_selection_reproduced
    assert row.minimum_consumed_center_separation > REQUIRED_CENTER_SEPARATION
    assert row.confirmation_center == (-140., -200., 80.)
    assert row.candidate_reach == (12, 4, 8)
    assert row.retained_prefix_budget == (2, 4, 1)
    assert row.self_fed_waves == 3
    assert row.required_exact_sites == 9
    assert not row.oracle_cropper_executor_scorer_imported
    assert not row.seed_target_candidates_scores_materialized
    assert not row.fresh_confirmation_claimed


if __name__ == "__main__":
    test_stage_local_confirmation_is_frozen_before_atom_access()
    print("stage-local IQC confirmation preregistration passed")
