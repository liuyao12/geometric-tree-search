from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_reference_modes_are_geometry_only_and_share_one_evaluation_path():
    assert 'const referenceMode = ["final", "first", "pooled"]' in APP
    assert "geometryReferenceIndices(geometryEvidence.length, referenceMode)" in APP
    assert "learnColoredDistanceEnvelopesEnsemble(referenceEvidence)" in APP
    assert "learnColoredCoordinationEnvelopesEnsemble(referenceEvidence" in APP
    assert "learnColoredAngularEnvelopesEnsemble(referenceEvidence" in APP
    assert "geometryFitUsesEnergyOrForce: false" in APP


def test_reference_choice_is_interactive_and_cache_safe():
    assert 'id="relaxationCalibrationReference"' in HTML
    for mode in ("final", "first", "pooled"):
        assert f'value="{mode}"' in HTML
    assert '$("relaxationCalibrationReference")' in APP
    assert "relaxationGeometryCalibrationCache.results.has(referenceMode)" in APP
    assert "relaxationGeometryCalibrationCache.results.set(referenceMode, result)" in APP
    assert 'relaxationCalibrationReference.addEventListener("change"' in APP


def test_receipt_and_ledger_expose_reference_sensitivity_without_upgrading_claims():
    assert 'selectedReferenceMode: relaxationGeometryCalibration.referenceMode' in APP
    assert "referenceSensitivity: relaxationGeometryReferenceSensitivity" in APP
    assert "referenceSensitivityModesSelectedWithoutCalculationLabels: true" in APP
    assert 'id: "geometry-calculation-calibration"' in APP
    assert "geometry-only sensitivity choices" in APP
    assert "first, and pooled references are geometry-only sensitivity choices" in ATLAS


def test_build_171_is_versioned_and_documented():
    assert 'buildId: "20260826-187"' in APP
    assert 'app.js?v=20260826-187' in HTML
    assert 'evidence-atlas.js?v=20260826-19' in HTML
    assert "Build 171" in README
    assert "Build 171" in DOCS
