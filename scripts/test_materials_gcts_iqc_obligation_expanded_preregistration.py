#!/usr/bin/env python3
"""Contracts for the expanded IQC obligation development manifest."""

from materials_gcts_iqc_obligation_expanded_preregistration import (
    EXPECTED_MANIFEST_DIGEST, audit)


def test_expanded_obligation_centers_freeze_before_atoms() -> None:
    row = audit()
    assert row.batch_size == 20
    assert len(row.development_centers) == row.batch_size
    assert row.center_selection_reproduced
    assert row.rollout_domains_disjoint
    assert row.minimum_consumed_center_separation > \
        row.required_center_separation
    assert row.minimum_batch_center_separation > \
        row.required_center_separation
    assert row.shuffle_trials == 31
    assert not row.oracle_or_cropper_imported
    assert not row.seed_target_candidates_or_scores_materialized
    assert not row.fresh_confirmation_claimed
    assert row.manifest_digest == EXPECTED_MANIFEST_DIGEST


if __name__ == "__main__":
    test_expanded_obligation_centers_freeze_before_atoms()
    print("expanded IQC obligation preregistration: passed")
