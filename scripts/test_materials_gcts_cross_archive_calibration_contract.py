from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
DATABASE = (APP_DIR / "structure-database.js").read_text(encoding="utf-8")
CALIBRATION = (APP_DIR / "geometry-calculation-calibration.js").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_nomad_method_provenance_is_canonical_and_fail_closed():
    assert "function canonicalJson(value)" in DATABASE
    assert "methodForCalculation(selectedRun, paired.calculation)" in DATABASE
    assert "methodRecordAvailable: Boolean(methodRecord)" in DATABASE
    assert "methodCanonicalJson:" in DATABASE
    assert 'methodCompatibilityPolicy: "exact canonical normalized NOMAD method record"' in DATABASE
    assert "program version and normalized method record are required" in APP


def test_frozen_artifact_predicts_without_refitting_or_target_access():
    assert "export function frozenGeometrySurrogateArtifact" in CALIBRATION
    assert "export function evaluateFrozenGeometrySurrogate" in CALIBRATION
    assert "artifact.standardizedCoefficients.reduce" in CALIBRATION
    assert "refitPerformed: false" in CALIBRATION
    assert "targetValuesUsedForPrediction: false" in CALIBRATION
    assert "targetValuesUsedForPosthocScoring: true" in CALIBRATION


def test_library_requires_exact_scientific_compatibility_and_disjoint_entry():
    for identifier in ("relaxationCalibrationPin", "relaxationCalibrationLibrarySelect",
                       "relaxationCalibrationTransferState"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    for field in ("targetMode", "targetKey", "referenceMode", "featureSchema", "reducedComposition",
                  "periodicAxes", "programName", "programVersion", "methodCanonicalJson",
                  "energyUnit", "forceUnit"):
        assert f"{field}:" in APP
    assert "source.entryId === current.entryId" in APP
    assert "resubstitution is not reported as transfer" in APP
    assert "No prediction was made" in APP


def test_receipt_omits_method_record_and_keeps_transfer_posthoc():
    assert "frozenCrossArchiveLibrary:" in APP
    assert "methodCanonicalRecordEmbedded: false" in APP
    assert "relaxationCalibrationLibrarySha256" in APP
    assert "relaxationTransferPredictionsSha256" in APP
    assert "absoluteEnergyComparedAcrossEntries: false" in APP
    assert "usedForGrowth: false" in APP
    assert "exact canonical normalized method record" in ATLAS


def test_build_176_retains_cross_archive_versioning_and_documentation():
    assert 'buildId: "20260827-268"' in APP
    assert 'app.js?v=20260827-268' in HTML
    assert 'structure-database.js?v=20260827-11' in APP
    assert 'geometry-calculation-calibration.js?v=20260826-6' in APP
    assert 'evidence-atlas.js?v=20260827-24' in HTML
    assert "Build 173" in README
    assert "Build 173" in DOCS
