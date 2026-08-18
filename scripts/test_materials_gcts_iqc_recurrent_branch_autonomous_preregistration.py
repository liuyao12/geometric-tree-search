#!/usr/bin/env python3

from materials_gcts_iqc_recurrent_branch_autonomous_preregistration import audit


def test_new_autonomous_nucleus_is_frozen_before_materialization():
    report = audit()
    assert report.source_commit == \
        "e7bb3a1b16c7ece4a5850198ed69b5a310dba1c6"
    assert report.confirmation_center == (40., -40., -80.)
    assert report.minimum_prior_center_separation > \
        report.required_center_separation
    assert report.domains_disjoint
    assert report.oracle_lift_bound == 44
    assert report.branch_neighbors == 9
    assert (report.beam_width, report.action_reach_per_configuration,
            report.search_depth) == (4, 4, 3)
    assert report.source_hashes_match
    assert report.development_gate_passed
    assert not report.seed_or_target_materialized
    assert not report.candidate_or_score_computed
    assert report.manifest_digest == \
        "6099d968bb0cef9cd73d3ea2dc17e117471b4daffd021f03e05e469ebf3b936e"


if __name__ == "__main__":
    test_new_autonomous_nucleus_is_frozen_before_materialization()
    print("recurrent branch autonomous preregistration passed")
