"""Source contract for the Stage-4 atoms-first viewport."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps" / "iqc-growth-live" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "apps" / "iqc-growth-live" / "index.html").read_text(encoding="utf-8")
README = (ROOT / "apps" / "iqc-growth-live" / "README.md").read_text(encoding="utf-8")


def test_growth_view_defaults_to_atoms_and_keeps_forensics_reversible() -> None:
    assert '<input id="growthEvidenceToggle" type="checkbox">' in HTML
    assert 'id="growthEvidenceToggleLabel">Growth view · atoms only' in HTML
    assert "function growthEvidenceVisible()" in APP
    assert "function keepAtomicMeshesOnly()" in APP
    assert "!child.userData.siteProvenancePickable" in APP
    assert "confinementGroup, externalDriveGroup, unitCellGroup, bondGroup, interfaceGroup" in APP
    assert "nucleationGroup, frontierGroup, decisionGroup" in APP
    assert "keepAtomicMeshesOnly();" in APP
    assert 'growthSceneMode: pipelineStage === 4 && !growthEvidenceToggle.checked ? "atoms-only" : "scientific-evidence"' in APP
    assert "candidateGeometryChangedByView: false, searchStateChangedByView: false" in APP
    assert "without changing enumeration, ranking, or execution" in APP
    assert "Build 307 · atoms-first material growth" in README
    assert 'buildId: "20260828-315"' in APP
    assert 'app.js?v=20260828-315' in HTML
    assert 'style.css?v=20260828-315' in HTML


if __name__ == "__main__":
    test_growth_view_defaults_to_atoms_and_keeps_forensics_reversible()
    print("atoms-first growth view contract: passed")
