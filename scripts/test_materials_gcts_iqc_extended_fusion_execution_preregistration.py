#!/usr/bin/env python3

from materials_gcts_iqc_extended_fusion_execution_preregistration import (
    FUSION_ARTIFACT_DIGEST, FUSION_MODEL_DIGEST, audit)

EXPECTED_MANIFEST_DIGEST = \
    "88bc9442f043d581ea544f865e7bb4d2f57cf81339407c23eb745a7edc2fd3ba"


def test_execution_is_frozen_before_any_new_atom_or_candidate():
    report = audit()
    assert report.source_hashes_match
    assert report.fusion_artifact_digest == FUSION_ARTIFACT_DIGEST
    assert report.fusion_model_digest == FUSION_MODEL_DIGEST
    assert report.fusion_capacity == ("incidence", 1, 2.)
    assert report.search_schedule == (4, 4, 8)
    assert report.action_count == 3
    assert len(report.centers) == 10
    assert not report.oracle_or_cropper_imported
    assert not report.seed_or_target_materialized
    assert not report.candidates_or_scores_computed
    assert report.manifest_digest == EXPECTED_MANIFEST_DIGEST


if __name__ == "__main__":
    test_execution_is_frozen_before_any_new_atom_or_candidate()
    print("extended IQC fusion execution-preregistration tests passed")
