#!/usr/bin/env python3
"""Contract for the unopened expanded IQC development corpus."""

import inspect

import materials_gcts_iqc_expanded_development_preregistration as protocol


def test_expanded_development_geometry_is_frozen_and_unopened():
    report = protocol.audit()
    assert len(report.prior_development_centers) == 10
    assert len(report.expanded_development_centers) == 8
    assert report.minimum_new_to_existing_or_reserved_separation > 37.4
    assert report.minimum_new_to_new_separation > 39.9
    assert report.domains_disjoint is True
    assert report.seed_or_target_materialized is False
    assert report.candidate_or_score_computed is False
    assert report.manifest_digest == \
        "c21e3fa12d2b2670af48974e5fd3856383c3518887fe28669abcd4e9a6464d43"
    source = inspect.getsource(protocol)
    for forbidden in (
            "oracle_patch", "_seed_crop", "_open_target",
            "_bounded_proposals", "candidate_incidence_descriptors"):
        assert forbidden not in source


def main():
    test_expanded_development_geometry_is_frozen_and_unopened()
    print("expanded IQC development preregistration passed")


if __name__ == "__main__":
    main()
