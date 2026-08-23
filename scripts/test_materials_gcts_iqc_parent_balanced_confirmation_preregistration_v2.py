"""Contract for the second fresh parent-balanced preregistration."""

import math

from materials_gcts_iqc_parent_balanced_confirmation_preregistration_v2 import (
    CONFIRMATION_CENTER, FAILED_V1_CENTER,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, PRIOR_CENTERS,
    select_confirmation_center, validate_preregistration)


def test_second_center_is_geometry_only_fresh_and_disjoint():
    assert select_confirmation_center() == CONFIRMATION_CENTER == \
        (-280., 160., -160.)
    assert FAILED_V1_CENTER in PRIOR_CENTERS
    assert min(math.dist(CONFIRMATION_CENTER, prior)
               for prior in PRIOR_CENTERS) > \
        MINIMUM_REQUIRED_DOMAIN_SEPARATION
    assert validate_preregistration()


def test_second_order_guard_fails_closed():
    guard = OneShotOrderGuard()
    guard.protocol_verified()
    guard.seed_opened()
    guard.receipt_frozen("b" * 64)
    guard.target_opened()
    guard.scored("b" * 64)
    assert guard.audit()["state"] == "scored"
    try:
        guard.target_opened()
        raise AssertionError("second target reopened")
    except RuntimeError:
        pass


if __name__ == "__main__":
    test_second_center_is_geometry_only_fresh_and_disjoint()
    test_second_order_guard_fails_closed()
    print("second parent-balanced preregistration: passed")
