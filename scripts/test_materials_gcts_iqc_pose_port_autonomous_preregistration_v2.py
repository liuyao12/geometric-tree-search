#!/usr/bin/env python3

from materials_gcts_iqc_pose_port_autonomous_preregistration_v2 import audit


def test_replacement_nucleus_is_frozen_and_disjoint():
    report = audit()
    assert report.prior_attempt_consumed_unknown
    assert report.confirmation_center == (-50., 50., -10.)
    assert report.oracle_lift_bound == 32
    assert report.minimum_prior_center_separation > \
        report.required_center_separation
    assert report.domains_disjoint
    assert report.source_hashes_match
    assert not report.seed_or_target_materialized
    assert not report.candidate_or_score_computed
    assert report.manifest_digest == \
        "39ad50d65f18b30a3d7f8b85abd5349de3e56f3edbc412460596378b0a99bb24"


if __name__ == "__main__":
    test_replacement_nucleus_is_frozen_and_disjoint()
    print("replacement autonomous preregistration passed")
