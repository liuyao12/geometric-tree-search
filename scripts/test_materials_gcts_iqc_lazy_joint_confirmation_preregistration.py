#!/usr/bin/env python3
"""Fast contract for the bounded joint IQC fresh protocol."""

import math

from materials_gcts_iqc_lazy_joint_confirmation_preregistration import (
    BASE_FALLBACK_TOP_K, CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST,
    JOINT_CHILD_TOP_K, MANIFEST, MAXIMUM_EXPANDED_PREFIXES,
    MINIMUM_REQUIRED_DOMAIN_SEPARATION, OneShotOrderGuard, PRIOR_CENTERS,
    select_confirmation_center, validate_preregistration)


def test_protocol():
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    assert len(PRIOR_CENTERS) == len(set(PRIOR_CENTERS)) == 89
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert min(math.dist(CONFIRMATION_CENTER, prior)
               for prior in PRIOR_CENTERS) > \
        MINIMUM_REQUIRED_DOMAIN_SEPARATION
    assert JOINT_CHILD_TOP_K == 1
    assert BASE_FALLBACK_TOP_K == 5
    assert MAXIMUM_EXPANDED_PREFIXES == 48
    assert MANIFEST["success_gate"]["grouped_consumed_exact_supply"] == "6/6"
    assert not MANIFEST["winner_selected_or_validated"]
    assert not MANIFEST["autonomous_growth_claimed"]
    assert not MANIFEST["stationary_or_exponential_claimed"]
    assert not MANIFEST["rerun_or_fallback_after_scoring_allowed"]


def test_guard_rejects_early_target():
    guard = OneShotOrderGuard()
    try:
        guard.target_opened()
    except RuntimeError:
        pass
    else:
        raise AssertionError("target opened before frozen receipt")


if __name__ == "__main__":
    test_protocol()
    test_guard_rejects_early_target()
    print("lazy joint IQC fresh preregistration: passed")
