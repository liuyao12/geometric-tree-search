#!/usr/bin/env python3
"""Contract tests for the third fresh full-width IQC protocol."""

from materials_gcts_iqc_parent_balanced_confirmation_preregistration_v3 import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, PRIOR_CENTERS,
    select_confirmation_center, validate_preregistration)


def test_geometry_and_sources_are_frozen_before_seed_access():
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert CONFIRMATION_CENTER not in PRIOR_CENTERS
    nearest_squared = min(sum(
        (CONFIRMATION_CENTER[axis] - prior[axis]) ** 2
        for axis in range(3)) for prior in PRIOR_CENTERS)
    assert nearest_squared > MINIMUM_REQUIRED_DOMAIN_SEPARATION ** 2


def test_guard_enforces_one_shot_target_order():
    guard = OneShotOrderGuard()
    guard.protocol_verified()
    guard.seed_opened()
    guard.receipt_frozen("a" * 64)
    guard.target_opened()
    guard.scored("a" * 64)
    assert guard.audit()["state"] == "scored"
    try:
        guard.target_opened()
    except RuntimeError:
        pass
    else:
        raise AssertionError("target reopened")


if __name__ == "__main__":
    test_geometry_and_sources_are_frozen_before_seed_access()
    test_guard_enforces_one_shot_target_order()
    print("V3 parent-balanced preregistration tests passed")
