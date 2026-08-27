from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
OBSERVABLES = (APP_DIR / "structure-observables.js").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_weighted_debye_observable_has_exact_auditable_normalization():
    assert "export function weightedPowderStructureFactor" in OBSERVABLES
    assert "term.weightProduct * powderKernel" in OBSERVABLES
    assert "1 + 2 * pairSum / selfWeightSquares" in OBSERVABLES
    assert "positive total squared self weight" in OBSERVABLES
    assert "Signed weights are allowed" in OBSERVABLES


def test_multicomponent_channels_are_interactive_and_general():
    assert 'id="scatteringContrastSelect"' in HTML
    assert '$("scatteringContrastSelect")' in APP
    assert "function syncScatteringContrastOptions()" in APP
    assert '["unit", "all atoms · unit number density"]' in APP
    assert '["electron", "all atoms · constant Z proxy"]' in APP
    assert '["chemical", "chemical contrast · Z − composition mean"]' in APP
    assert "tokens.forEach" in APP
    assert "species:" in APP
    assert "PERIODIC_ELEMENTS" in APP


def test_receipt_and_ledger_preserve_nonclaims_and_history_basis():
    assert "displayedContrast:" in APP
    assert "displayedSqSha256" in APP
    assert "qDependentAtomicFormFactorsUsed: false" in APP
    assert "neutronScatteringLengthsUsed: false" in APP
    assert "occupancyWeightedScatteringUsed: false" in APP
    assert "DebyeWallerDampingUsed: scatteringUsesReportedDisplacement()" in APP
    assert "diffuseRedistributionIncluded: false" in APP
    assert "instrumentResponseUsed: false" in APP
    assert "usedAsGrowthInput: false" in APP
    assert "structural-leap comparison remains unit-weight" in APP
    assert "not a standard binary Bhatia–Thornton factor" in APP


def test_build_169_is_retained_in_current_release():
    assert 'buildId: "20260827-260"' in APP
    assert 'app.js?v=20260827-260' in HTML
    assert 'structure-observables.js?v=20260827-7' in APP
    assert 'evidence-atlas.js?v=20260827-22' in HTML
    assert "chemical sublattice order" in ATLAS
    assert "Build 169" in README
    assert "Build 169" in DOCS
