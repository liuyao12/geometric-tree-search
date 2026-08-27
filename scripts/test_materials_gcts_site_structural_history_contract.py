from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
STYLE = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/site-structural-history.js").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()
DOCS = (ROOT / "docs/projects/materials-recursive-gcts-benchmark.md").read_text()


def test_only_locally_affected_emitted_sites_enter_bounded_history():
    assert "pendingSiteHistoryIds.add(atom.id)" in APP
    assert "neighbor.creationGeometry" in APP
    assert "recordPendingSiteStructuralHistories(frozen)" in APP
    assert "MAXIMUM_RETAINED_STRUCTURAL_LEAPS" in APP
    assert "stateSignature(previous) === stateSignature(normalized)" in MODULE
    assert "slice(-maximumRecords)" in MODULE


def test_history_reuses_exact_creation_response_metrics():
    assert "selectedSiteCreationResponse(atom)" in APP
    for metric in ("persistentNeighborCount", "lostNeighborCount", "gainedNeighborCount",
                   "radialRmsAngstrom", "rootD2MinAngstrom", "equivalentShearStrain",
                   "localVolumeChangeFraction"):
        assert metric in APP
        assert metric in MODULE
    assert "targetUsed: false" in MODULE
    assert "physicalTimeModeled: false" in MODULE
    assert "dynamicsIntegrated: false" in MODULE


def test_interactive_pathway_is_visible_and_accessible():
    for identifier in ("siteStructuralHistoryState", "siteStructuralHistoryPlot",
                       "siteStructuralHistorySteps", "siteStructuralHistoryBoundary"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "site-history-radial" in STYLE
    assert "site-history-nonaffine" in STYLE
    assert 'role: "button"' in APP
    assert 'event.key === "Enter"' in APP
    assert "Leap index is search order, not physical time" in APP


def test_growth_workbench_signed_formatting_is_globally_defined():
    assert 'const signed = (value, digits = 3)' in APP
    assert "renderIonicPairConvergence" in APP


def test_build_193_assets_and_narrative():
    assert 'buildId: "20260827-258"' in APP
    assert 'app.js?v=20260827-258' in HTML
    assert 'style.css?v=20260827-258' in HTML
    assert 'site-structural-history.js?v=20260826-1' in APP
    assert "Build 193" in README
    assert "Build 193" in DOCS
