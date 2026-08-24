#!/usr/bin/env python3
"""Contract for the fresh two-fallback IQC preregistration."""

from materials_gcts_iqc_hybrid_confirmation_preregistration_v4 import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, MANIFEST,
    MAXIMUM_FALLBACKS, OneShotOrderGuard, select_confirmation_center,
    validate_preregistration)


def test_hybrid_confirmation_is_frozen_before_any_oracle_access():
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert CONFIRMATION_CENTER == (360., 0., 0.)
    assert MAXIMUM_FALLBACKS == 2
    assert MANIFEST["maximum_action_marginal_fallbacks"] == 2
    assert not MANIFEST["target_or_oracle_opened_during_preregistration"]
    assert not MANIFEST["rerun_or_fallback_after_scoring_allowed"]
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST


def test_order_guard_rejects_target_before_receipt():
    guard = OneShotOrderGuard()
    guard.protocol_verified()
    try:
        guard.target_opened()
    except RuntimeError:
        pass
    else:
        raise AssertionError("target opened before seed and receipt")
    guard.seed_opened()
    guard.receipt_frozen("0" * 64)
    guard.target_opened()
    guard.scored("0" * 64)
    assert guard.audit()["state"] == "scored"


if __name__ == "__main__":
    test_hybrid_confirmation_is_frozen_before_any_oracle_access()
    test_order_guard_rejects_target_before_receipt()
    print("IQC hybrid V4 preregistration tests passed")
