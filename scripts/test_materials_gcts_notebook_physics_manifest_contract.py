#!/usr/bin/env python3
"""Contract for coordinate-free two-run physics-manifest comparison."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_notebook_physics_manifest_contract() -> None:
    assert 'buildId: "20260826-160"' in APP
    assert 'app.js?v=20260826-160' in HTML
    assert 'style.css?v=20260826-67' in HTML
    for element_id in ("notebookPhysicsAudit", "notebookPhysicsFilters", "notebookPhysicsMatrix", "notebookPhysicsDetail"):
        assert f'id="{element_id}"' in HTML
    for filter_name in ("changed", "all", "open"):
        assert f'data-notebook-physics-filter="{filter_name}"' in HTML
    assert "function notebookPhysicsManifest" in APP
    assert "physicsManifest: notebookPhysicsManifest(structuralLeaps)" in APP
    assert "function notebookPhysicsComparison" in APP
    assert "function notebookPhysicsLayerHistory" in APP
    assert "function renderNotebookPhysicsEvolution" in APP
    assert "function renderNotebookPhysicsAudit" in APP
    assert "renderNotebookPhysicsAudit(selected)" in APP
    assert 'coordinatesEmbedded === false' in APP
    assert 'targetUsed === false' in APP
    assert 'physicalTimeModeled: false' in APP
    assert 'historyAlignment: "discrete structural-leap index; not physical time"' in APP
    assert 'targetUsed: structuralLeaps.some((entry) => entry.targetUsed === true)' in APP
    assert 'status/role/encoding define configuration; evidence defines response' in APP
    assert 'It does not compare physical energies, infer omitted mechanisms, or align structural leaps to elapsed time.' in APP
    assert ".notebook-physics-audit" in CSS
    assert ".notebook-physics-matrix" in CSS
    assert ".notebook-physics-detail" in CSS
    assert ".notebook-physics-evolution-track" in CSS
    assert "Build 154" in README
    assert "physics-manifest comparison" in README


if __name__ == "__main__":
    test_notebook_physics_manifest_contract()
    print("notebook physics manifest contract passed")
