#!/usr/bin/env python3

from materials_gcts_iqc_complete_frontier_confirmation_preregistration import (
    ACTION_REACH_SCHEDULE, CONFIRMATION_CENTER, EXPECTED_MANIFEST_DIGEST,
    SOURCE_SHA256, audit)


def test_complete_frontier_confirmation_is_geometry_only_and_frozen():
    report = audit()
    assert report.confirmation_center == CONFIRMATION_CENTER == \
        (-110., -10., -10.)
    assert report.minimum_prior_separation == 40.
    assert report.center_selection_reproduced
    assert report.target_domain_disjoint
    assert report.action_reach_schedule == ACTION_REACH_SCHEDULE == (8, 8, 8)
    assert report.unpruned_from_depth == 0
    assert report.dual_portfolio_per_channel == 9
    assert report.maximum_dual_portfolio_states == 18
    assert len(SOURCE_SHA256) == 6
    assert not report.oracle_or_cropper_imported
    assert not report.seed_or_target_materialized
    assert not report.candidates_or_scores_computed
    assert report.manifest_digest == EXPECTED_MANIFEST_DIGEST


if __name__ == "__main__":
    test_complete_frontier_confirmation_is_geometry_only_and_frozen()
    print("complete-frontier confirmation-preregistration tests passed")
