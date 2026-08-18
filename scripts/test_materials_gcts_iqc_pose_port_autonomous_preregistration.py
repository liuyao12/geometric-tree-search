#!/usr/bin/env python3

from materials_gcts_iqc_pose_port_autonomous_preregistration import audit


def test_autonomous_confirmation_is_frozen_without_materialization():
    report = audit()
    assert report.confirmation_center == (-70., -70., 30.)
    assert report.minimum_prior_center_separation > \
        report.required_center_separation
    assert report.domains_disjoint
    assert report.source_hashes_match
    assert report.beam_width == 4
    assert report.action_reach_per_configuration == 4
    assert report.search_depth == 3
    assert not report.seed_or_target_materialized
    assert not report.candidate_or_score_computed
    assert report.manifest_digest == \
        "cf220de05d44fdf52747464c9975c040aea33b53efd37533cf79157c7208f077"


if __name__ == "__main__":
    test_autonomous_confirmation_is_frozen_without_materialization()
    print("IQC pose-port autonomous preregistration passed")
