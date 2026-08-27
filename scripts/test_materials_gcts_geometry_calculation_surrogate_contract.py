from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
CALIBRATION = (APP_DIR / "geometry-calculation-calibration.js").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_surrogate_is_fixed_low_capacity_and_every_prediction_is_held_out():
    assert "export function geometryCalculationSurrogate" in CALIBRATION
    assert "requiredPairs = Math.max(minimumPairs, featureKeys.length + 2)" in CALIBRATION
    assert "rows.filter((_, index) => index !== heldout)" in CALIBRATION
    assert "fitStandardizedRidge(training" in CALIBRATION
    assert 'crossValidationKind: "leave-one-frame-out"' in CALIBRATION
    assert "crossValidatedQSquared" in CALIBRATION


def test_geometry_channels_and_calculation_targets_remain_explicit():
    assert 'RELAXATION_SURROGATE_FEATURES = ["meanDistanceMismatch", "meanAngleMismatch", "meanCoordinationDeficit"]' in APP
    assert '"relativeEnergyElectronVoltPerPrimitiveAtom", { ridge: 1, minimumPairs: 5 }' in APP
    assert '"forceRmsElectronVoltPerAngstrom", { ridge: 1, minimumPairs: 5 }' in APP
    assert "calculationLabelsUsedForSurrogateFit: true" in CALIBRATION
    assert "geometryEnvelopeFitUsesCalculationLabels: false" in CALIBRATION
    assert "correlatedArchiveFrames: true" in CALIBRATION
    assert "usedForGrowth: false" in CALIBRATION


def test_prediction_overlay_and_receipt_are_auditable():
    assert 'id="relaxationSurrogateState"' in HTML
    assert 'id="relaxationSurrogateCoefficients"' in HTML
    assert "calibration-prediction-link" in APP
    assert "calibration-prediction" in APP
    assert "geometricSurrogatePreflight:" in APP
    assert "relaxationSurrogatePredictionsSha256" in APP
    assert "predictionsEmbedded: false" in APP
    assert "fixed ridge surrogate fits source labels" in ATLAS


def test_build_172_is_versioned_and_documented():
    assert 'buildId: "20260827-227"' in APP
    assert 'app.js?v=20260827-227' in HTML
    assert 'geometry-calculation-calibration.js?v=20260826-6' in APP
    assert 'evidence-atlas.js?v=20260826-19' in HTML
    assert "Build 172" in README
    assert "Build 172" in DOCS
