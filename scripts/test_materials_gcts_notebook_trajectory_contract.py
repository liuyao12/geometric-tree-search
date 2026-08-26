#!/usr/bin/env python3
"""Contract for coordinate-free structural-leap comparison in the run notebook."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_notebook_trajectory_contract() -> None:
    assert 'buildId: "20260825-138"' in APP
    assert 'app.js?v=20260825-138' in HTML
    for element_id in ("notebookTrajectoryAudit", "notebookTrajectoryPlot", "notebookTrajectorySummary"):
        assert f'id="{element_id}"' in HTML
    assert "const structuralLeaps = search?.structuralLeapCertificates || []" in APP
    assert 'alignment: "structural leap index"' in APP
    assert "MAXIMUM_RETAINED_STRUCTURAL_LEAPS = 24" in APP
    assert "structuralLeapHistory" in APP
    assert "historyTruncated" in APP
    assert "function notebookTrajectoryComparison" in APP
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
    assert "structural-leap series" in README
    assert "not physical\ntime" in README


if __name__ == "__main__":
    test_notebook_trajectory_contract()
    print("notebook trajectory contract passed")
