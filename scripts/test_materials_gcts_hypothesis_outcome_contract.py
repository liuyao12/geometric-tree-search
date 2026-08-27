from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/hypothesis-separation-outcome.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_registered_outcome_is_visible_and_interactive():
    assert 'id="notebookHypothesisOutcome"' in HTML
    assert '$("notebookHypothesisOutcome")' in APP
    assert "renderNotebookHypothesisOutcome(selected)" in APP
    assert "compareHypothesisSeparationOutcomes" in APP
    assert ".notebook-hypothesis-grid" in STYLE
    assert "matched horizon" in APP
    assert "S(q) peak prominence" in MODULE
    assert "mean q₆ / |ψ₆|" in MODULE


def test_comparison_fails_closed_and_has_scientific_boundaries():
    for token in ("registration-mismatch", "registration-drift", "input-mismatch", "execution-missing",
                  "target-tainted", "controls-mismatch", "history-truncated", "horizon-unavailable"):
        assert token in MODULE
    assert 'changed[0] !== "hypothesisSeparation"' in MODULE
    assert "physicalTimeInferred: false" in MODULE
    assert "causalPhysicalMechanismInferred: false" in MODULE
    assert "candidatesPooled: false" in MODULE
    assert "searchReplayed: false" in MODULE
    assert "not physical time, energy, kinetics" in MODULE


def test_build_184_assets_and_narrative():
    assert 'buildId: "20260827-235"' in APP
    assert 'app.js?v=20260827-235' in HTML
    assert 'style.css?v=20260826-104' in HTML
    assert 'hypothesis-separation-outcome.js?v=20260826-1' in APP
    assert "Build 184" in README
    assert "Build 184" in DOCS
