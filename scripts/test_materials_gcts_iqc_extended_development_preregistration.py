#!/usr/bin/env python3

from pathlib import Path

from materials_gcts_iqc_extended_development_preregistration import (
    DEVELOPMENT_CENTERS, FROZEN_FUSION_CAPACITY,
    FROZEN_FUSION_MODEL_DIGEST, PRIOR_CENTERS, audit)


def test_extended_development_is_geometry_only_and_disjoint():
    report = audit()
    assert len(PRIOR_CENTERS) == 50
    assert len(DEVELOPMENT_CENTERS) == 10
    assert report.target_balls_disjoint
    assert report.minimum_prior_separation > report.required_center_separation
    assert report.minimum_batch_separation > report.required_center_separation
    assert report.maximum_center_norm <= 92.
    assert report.selection_rule_reproduced
    assert report.oracle_lift_bound == 44
    assert report.frozen_fusion_model_digest == FROZEN_FUSION_MODEL_DIGEST
    assert report.frozen_fusion_capacity == FROZEN_FUSION_CAPACITY
    assert not report.oracle_or_cropper_imported
    assert not report.seed_or_target_materialized
    assert not report.candidates_or_scores_computed
    source = Path(__file__).with_name(
        "materials_gcts_iqc_extended_development_preregistration.py"
    ).read_text()
    for forbidden in (
            "materials_gcts_icosahedral_modelset", "oracle_patch",
            "_seed_crop", "_open_target", "candidate_incidence_descriptors"):
        assert forbidden not in source


if __name__ == "__main__":
    test_extended_development_is_geometry_only_and_disjoint()
    print("extended IQC development preregistration passed")
