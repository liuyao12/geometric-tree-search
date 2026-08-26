from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
CALIBRATION = (APP_DIR / "geometry-calculation-calibration.js").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_statistics_are_explicit_and_withheld_for_short_or_constant_series():
    assert "export function geometryCalculationCalibration" in CALIBRATION
    assert "pairs.length < 3" in CALIBRATION
    assert "averageRanks" in CALIBRATION
    assert "rSquared" in CALIBRATION
    assert "descriptiveOnly: true" in CALIBRATION
    assert "physicalCausalityClaimed: false" in CALIBRATION


def test_geometry_reference_is_final_frame_only_and_labels_do_not_fit_it():
    assert "function relaxationGeometryCalculationCalibration()" in APP
    assert "const finalFrame = frames.at(-1)" in APP
    assert "learnColoredDistanceEnvelopesEnsemble(finalEvidence)" in APP
    assert "learnColoredCoordinationEnvelopesEnsemble(finalEvidence" in APP
    assert "learnColoredAngularEnvelopesEnsemble(finalEvidence" in APP
    assert "geometryFitUsesEnergyOrForce: false" in APP
    assert "labelsUsedToRankGrowth: false" in APP
    assert "physicalTimeUsed: false" in APP


def test_interactive_plot_receipt_and_ledger_are_auditable():
    for identifier in (
        "relaxationCalibrationMetric",
        "relaxationCalibrationState",
        "relaxationCalibrationChart",
        "relaxationCalibrationBoundary",
    ):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "function renderRelaxationCalibration()" in APP
    assert "geometryCalculationCalibration:" in APP
    assert "relaxationGeometryCalibrationSha256" in APP
    assert 'id: "geometry-calculation-calibration"' in APP
    assert "final-frame-referenced geometric mismatch" in ATLAS


def test_build_170_is_versioned_and_documented():
    assert 'buildId: "20260826-170"' in APP
    assert 'app.js?v=20260826-170' in HTML
    assert 'geometry-calculation-calibration.js?v=20260826-1' in APP
    assert 'evidence-atlas.js?v=20260826-12' in HTML
    assert "Build 170" in README
    assert "Build 170" in DOCS

