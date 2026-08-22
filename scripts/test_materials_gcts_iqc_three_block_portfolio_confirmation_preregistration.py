#!/usr/bin/env python3
"""Fast contract for the fresh three-block IQC preregistration."""

import math

from materials_gcts_iqc_three_block_portfolio_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, MANIFEST,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, PRIOR_CENTERS,
    select_confirmation_center, validate_preregistration)


def test_geometry_and_manifest_are_frozen() -> None:
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert len(PRIOR_CENTERS) == len(set(PRIOR_CENTERS)) == 86
    assert min(math.dist(CONFIRMATION_CENTER, prior)
               for prior in PRIOR_CENTERS) > \
        MINIMUM_REQUIRED_DOMAIN_SEPARATION
    assert MANIFEST["success_gate"]["exact_lineages_minimum"] == 1
    assert MANIFEST["expected_lineage_actions"] == 9
    assert not MANIFEST["winner_selected_or_validated"]
    assert not MANIFEST["autonomous_growth_claimed"]
    assert not MANIFEST["stationary_or_exponential_claimed"]
    assert not MANIFEST["rerun_or_fallback_after_scoring_allowed"]


def test_one_shot_order_is_mechanical() -> None:
    guard = OneShotOrderGuard()
    for method in (guard.seed_opened, guard.target_opened):
        try:
            method()
        except RuntimeError:
            pass
        else:
            raise AssertionError("order guard accepted a premature event")
    guard.protocol_verified()
    guard.seed_opened()
    digest = "a" * 64
    guard.receipt_frozen(digest)
    guard.target_opened()
    guard.scored(digest)
    assert guard.audit() == {
        "state": "scored", "seed_open_count": 1,
        "target_open_count": 1, "score_count": 1,
        "receipt_digest": digest}
    for method in (guard.seed_opened, guard.target_opened,
                   lambda: guard.scored(digest)):
        try:
            method()
        except RuntimeError:
            pass
        else:
            raise AssertionError("order guard accepted a repeated event")


if __name__ == "__main__":
    test_geometry_and_manifest_are_frozen()
    test_one_shot_order_is_mechanical()
    print("fresh three-block portfolio preregistration: passed")
