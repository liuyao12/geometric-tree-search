from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
CSS = (APP_DIR / "style.css").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_feature_support_map_is_interactive_and_geometry_only():
    for identifier in ("relaxationCalibrationFeaturePair", "relaxationCalibrationSupportChart",
                       "relaxationCalibrationDeploymentState"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    for mode in ("distance-angle", "distance-coordination", "angle-coordination"):
        assert mode in HTML
        assert mode in APP
    assert "function renderRelaxationCalibrationSupportMap" in APP
    assert "calculationTargetValuesDisplayedOrUsed: false" in APP
    assert ".support-box" in CSS
    assert ".support-target" in CSS
    assert ".support-candidate" in CSS
    assert ".support-abstain" in CSS


def test_matched_intervention_removes_only_external_term():
    assert "function externalCalibrationRankingInterventionAudit" in APP
    assert 'entry.id === "external-calibration"' in APP
    assert "withoutScore: candidate.baselineScore - contribution" in APP
    assert "candidateSetDigest: lastPolicyComparison.candidateDigest" in APP
    assert "candidateSetChanged: false" in APP
    assert "hardAdmissionChanged: false" in APP
    assert "rankInversions" in APP
    assert "matchedRankingIntervention:" in APP
    assert "executed: false" in APP


def test_public_narrative_keeps_claim_boundary():
    assert "deployment map overlays target frames and live candidates" in ATLAS
    assert "Build 176" in README
    assert "Build 176" in DOCS
    assert "Calculation\ntargets are neither displayed nor used by this map" in README


def test_build_176_is_versioned():
    assert 'buildId: "20260826-210"' in APP
    assert 'app.js?v=20260826-210' in HTML
    assert 'style.css?v=20260826-104' in HTML
    assert 'evidence-atlas.js?v=20260826-19' in HTML
