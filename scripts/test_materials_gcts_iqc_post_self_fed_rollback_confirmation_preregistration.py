#!/usr/bin/env python3
"""Regression for the target-sealed IQC rollback confirmation protocol."""

import math

from materials_gcts_iqc_post_self_fed_rollback_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST, MANIFEST, PRIOR_CENTERS,
    SECOND_BLOCK_RADIUS, select_confirmation_center,
    validate_preregistration)


def test_rollback_confirmation_is_geometry_only_and_frozen():
    assert select_confirmation_center() == CONFIRMATION_CENTER
    assert validate_preregistration() == EXPECTED_MANIFEST_DIGEST
    assert min(math.dist(CONFIRMATION_CENTER, center)
               for center in PRIOR_CENTERS) > 2 * SECOND_BLOCK_RADIUS
    assert MANIFEST["target_open_limit"] == 1
    assert MANIFEST["rollback_metric"] == "frontier_vote_mass"
    assert MANIFEST["rollback_horizon"] == 12
    assert MANIFEST["stationary_or_exponential_claimed"] is False


if __name__ == "__main__":
    test_rollback_confirmation_is_geometry_only_and_frozen()
    print("rollback confirmation preregistration tests passed")
