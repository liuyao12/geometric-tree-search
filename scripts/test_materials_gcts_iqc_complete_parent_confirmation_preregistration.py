#!/usr/bin/env python3
"""Fast contract for the second fresh complete-parent protocol."""

import math

from materials_gcts_iqc_complete_parent_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, MANIFEST,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, POSITION_TOLERANCE,
    PRIOR_CENTERS, select_confirmation_center, validate_preregistration)


def test_successor_protocol_is_frozen_before_seed_access() -> None:
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    assert len(PRIOR_CENTERS) == len(set(PRIOR_CENTERS)) == 87
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert min(math.dist(CONFIRMATION_CENTER, prior)
               for prior in PRIOR_CENTERS) > \
        MINIMUM_REQUIRED_DOMAIN_SEPARATION
    assert POSITION_TOLERANCE == 1e-5
    assert MANIFEST["complete_parent_width"] == 8
    assert MANIFEST["success_gate"][
        "exact_nine_action_lineages_minimum"] == 1
    assert not MANIFEST["winner_selected_or_validated"]
    assert not MANIFEST["autonomous_growth_claimed"]
    assert not MANIFEST["stationary_or_exponential_claimed"]


def test_successor_order_guard_rejects_premature_events() -> None:
    guard = OneShotOrderGuard()
    try:
        guard.target_opened()
    except RuntimeError:
        pass
    else:
        raise AssertionError("premature target accepted")
    guard.protocol_verified(); guard.seed_opened()
    digest = "b" * 64
    guard.receipt_frozen(digest); guard.target_opened(); guard.scored(digest)
    assert guard.audit()["state"] == "scored"
    assert guard.audit()["target_open_count"] == 1


if __name__ == "__main__":
    test_successor_protocol_is_frozen_before_seed_access()
    test_successor_order_guard_rejects_premature_events()
    print("fresh complete-parent preregistration: passed")
