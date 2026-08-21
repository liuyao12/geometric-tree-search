#!/usr/bin/env python3

from materials_gcts_iqc_port_obligation_confirmation_preregistration import (
    CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST,
    REQUIRED_CENTER_SEPARATION,
    validate_preregistration)


def test_geometry_only_confirmation_manifest():
    row = validate_preregistration()
    assert row.confirmation_center == CONFIRMATION_CENTER == (-110., -70., -70.)
    assert row.minimum_consumed_center_separation > REQUIRED_CENTER_SEPARATION
    assert row.minimum_consumed_center_separation == 87.17797887081348
    assert row.rollout_domains_disjoint is True
    assert row.center_selection_reproduced is True
    assert row.source_hashes_match is True
    assert row.seed_or_target_materialized is False
    assert row.candidates_or_scores_computed is False
    assert row.rollout_horizon == 16
    assert row.maximum_frozen_candidates == 16
    assert row.target_open_limit == 1
    assert row.manifest_digest == EXPECTED_MANIFEST_DIGEST


def main():
    test_geometry_only_confirmation_manifest()
    print("IQC port-obligation confirmation preregistration passed")


if __name__ == "__main__":
    main()
