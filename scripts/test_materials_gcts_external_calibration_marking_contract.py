from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
CALIBRATION = (APP_DIR / "geometry-calculation-calibration.js").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_promotion_gate_is_predeclared_and_no_refit():
    assert "export const GEOMETRY_SURROGATE_PROMOTION_GATE" in CALIBRATION
    assert "minimumTargetFrames: 5" in CALIBRATION
    assert "minimumSupportedTargetFrames: 5" in CALIBRATION
    assert "minimumFeatureSupportCoverage: .8" in CALIBRATION
    assert "minimumPredictionSpearman: .8" in CALIBRATION
    assert "minimumPredictiveQSquared: 0" in CALIBRATION
    assert "transfer?.refitPerformed === false" in CALIBRATION
    assert "transfer?.targetValuesUsedForPrediction === false" in CALIBRATION
    assert "transfer.predictiveQSquared >" in CALIBRATION


def test_source_support_is_frozen_and_outside_candidates_abstain():
    assert "GEOMETRY_SURROGATE_SUPPORT_MARGIN_STANDARD_DEVIATIONS = .25" in CALIBRATION
    assert "export function frozenGeometryFeatureSupport" in CALIBRATION
    assert "featureMinimums" in CALIBRATION
    assert "featureMaximums" in CALIBRATION
    assert "support.inSupport ? Math.max(-3, Math.min(3, standardized)) : 0" in CALIBRATION
    assert "abstained: !support.inSupport" in CALIBRATION
    assert "currentExternalCandidateSupportAudit" in APP
    assert "currentFrontierAbstainedCandidates" in APP


def test_candidate_channels_reuse_exact_archive_mismatch_field():
    assert "function calibratedGeometryFeaturesForFreshSites" in APP
    assert "coloredLocalConstraintMismatch(projected.map" in APP
    assert 'meanDistanceMismatch: average("distance")' in APP
    assert 'meanAngleMismatch: average("angle")' in APP
    assert "meanCoordinationDeficit: field.meanCoordinationDeficit" in APP
    assert "sameDefinitionsAsArchiveSurrogate: true" in APP


def test_opt_in_mark_changes_ranking_only():
    for identifier in ("relaxationCalibrationPromote", "relaxationCalibrationPromotionState"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert 'scoreTerm("external-calibration"' in APP
    assert "+ evaluation.externalCalibration.weight * evaluation.externalCalibration.score" in APP
    assert "candidateSetChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "physicalPotentialUsed: false" in APP
    assert "targetValuesUsedForCandidatePrediction: false" in APP


def test_receipt_and_public_boundary_distinguish_rank_from_physics():
    assert "externallyCalibratedGeometryRanking:" in APP
    assert "eligibleAsGrowthMark:" in APP
    assert "promotedAsGrowthMark:" in APP
    assert "usedForCandidateGeneration: false" in APP
    assert "usedForHardAdmission: false" in APP
    assert "at least five target frames" in ATLAS
    assert "Build 174" in README
    assert "Build 174" in DOCS


def test_build_176_retains_external_calibration_marking():
    assert 'buildId: "20260826-202"' in APP
    assert 'app.js?v=20260826-202' in HTML
    assert 'style.css?v=20260826-98' in HTML
    assert 'evidence-atlas.js?v=20260826-19' in HTML
    assert 'geometry-calculation-calibration.js?v=20260826-6' in APP
    assert "Build 175" in README
    assert "Build 175" in DOCS
