#!/usr/bin/env python3
"""Contract for coordinate-free structural-leap comparison in the run notebook."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_notebook_trajectory_contract() -> None:
    assert 'buildId: "20260826-158"' in APP
    assert 'app.js?v=20260826-158' in HTML
    for element_id in ("notebookTrajectoryAudit", "notebookTrajectoryPlot", "notebookTrajectorySummary",
                       "notebookTrajectoryHarmonics", "notebookTrajectoryStateDetail"):
        assert f'id="{element_id}"' in HTML
    assert 'data-notebook-trajectory-mode="series"' in HTML
    assert 'data-notebook-trajectory-mode="pathway"' in HTML
    for harmonic in (4, 6, 12):
        assert f'data-notebook-pathway-harmonic="{harmonic}"' in HTML
    assert "const structuralLeaps = search?.structuralLeapCertificates || []" in APP
    assert 'alignment: "structural leap index"' in APP
    assert "MAXIMUM_RETAINED_STRUCTURAL_LEAPS = 24" in APP
    assert "structuralLeapHistory" in APP
    assert "historyTruncated" in APP
    assert "function notebookTrajectoryComparison" in APP
    assert "function notebookMultiscaleOrderPathway" in APP
    assert "function showNotebookPathwayState" in APP
    assert 'notebookTrajectoryMode = "series"' in APP
    assert "notebookTrajectoryHarmonic = 6" in APP
    assert 'horizontalObservable: "mean local q_l in 3D or |psi_l| in 2D"' in APP
    assert 'verticalObservable: "unit-weight geometric S(q) dominant-peak prominence"' in APP
    assert "properRotationInvariant: true" in APP
    assert "phaseDiagram: false" in APP
    assert "function renderNotebookTrajectoryAudit" in APP
    assert "firstDivergence" in APP
    assert "atomDelta" in APP
    assert "firstAmplification" in APP
    assert "physicalTimeModeled: false" in APP
    assert "dynamicsIntegrated: false" in APP
    assert "coordinatesEmbedded: false" in APP
    assert "Existing run upgraded with its coordinate-free structural-leap history." in APP
    assert ".notebook-trajectory-audit" in CSS
    assert ".notebook-trajectory-audit svg .divergence" in CSS
    assert ".notebook-trajectory-modes" in CSS
    assert ".notebook-trajectory-state" in CSS
    assert "structural-leap series" in README
    assert "not physical\ntime" in README
    assert "Build 140 makes that multiscale microscope comparative" in README
    assert "not a phase diagram" in README


if __name__ == "__main__":
    test_notebook_trajectory_contract()
    print("notebook trajectory contract passed")
