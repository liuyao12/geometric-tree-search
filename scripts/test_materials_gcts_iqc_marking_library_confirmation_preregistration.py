#!/usr/bin/env python3
"""Fast contract for the third fresh IQC confirmation protocol."""

import math

from materials_gcts_iqc_marking_library_confirmation_preregistration import (
    CHANNEL_NAMES, CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST,
    LOCAL_SECTION_CHILD_TOP_K, MANIFEST, MINIMUM_REQUIRED_DOMAIN_SEPARATION,
    OneShotOrderGuard, PRIOR_CENTERS, select_confirmation_center,
    validate_preregistration)


def test_protocol_is_frozen_before_any_new_geometry() -> None:
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    assert len(PRIOR_CENTERS) == len(set(PRIOR_CENTERS)) == 88
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert min(math.dist(CONFIRMATION_CENTER, prior)
               for prior in PRIOR_CENTERS) > \
        MINIMUM_REQUIRED_DOMAIN_SEPARATION
    assert CHANNEL_NAMES[-1] == "local-section"
    assert LOCAL_SECTION_CHILD_TOP_K == 2
    assert MANIFEST["complete_parent_width"] == 8
    assert MANIFEST["success_gate"][
        "exact_nine_action_lineages_minimum"] == 1
    assert not MANIFEST["winner_selected_or_validated"]
    assert not MANIFEST["autonomous_growth_claimed"]
    assert not MANIFEST["stationary_or_exponential_claimed"]
    assert not MANIFEST["rerun_or_fallback_after_scoring_allowed"]


def test_order_guard_rejects_early_target() -> None:
    guard = OneShotOrderGuard()
    try:
        guard.target_opened()
    except RuntimeError:
        pass
    else:
        raise AssertionError("target opened before protocol and receipt")


if __name__ == "__main__":
    test_protocol_is_frozen_before_any_new_geometry()
    test_order_guard_rejects_early_target()
    print("five-channel IQC fresh preregistration: passed")
