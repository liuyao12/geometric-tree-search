#!/usr/bin/env python3
"""Contract for fail-closed multi-run controlled geometric response studies."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_notebook_controlled_sweep_contract() -> None:
    assert 'buildId: "20260825-141"' in APP
    assert 'app.js?v=20260825-141' in HTML
    assert 'style.css?v=20260825-50' in HTML
    for element_id in ("notebookSweepAudit", "notebookSweepFactor", "notebookSweepOutcome",
                       "notebookSweepPlot", "notebookSweepSummary"):
        assert f'id="{element_id}"' in HTML
    assert "const NOTEBOOK_SWEEP_OUTCOMES" in APP
    assert "function notebookControlledResponseSweeps" in APP
    assert "function compactNotebookSweepSetting" in APP
    assert "function renderNotebookControlledSweep" in APP
    assert 'new Set(["pipeline", "structuralObservable", "costModel"])' in APP
    assert "if (settingMap.size < 3) return" in APP
    assert "inputIdentity" in APP
    assert "fixedFactorCount" in APP
    assert "coordinatesEmbedded: false" in APP
    assert "physicalTimeModeled: false" in APP
    assert "categorical settings" in APP
    assert "does not interpolate between settings" in APP
    assert ".notebook-sweep-audit" in CSS
    assert ".notebook-sweep-settings" in CSS
    assert "Build 141 adds a controlled-response study" in README
    assert "byte-identical values for every other recorded" in README
    assert "not interpolation, an equilibrium phase diagram" in README


if __name__ == "__main__":
    test_notebook_controlled_sweep_contract()
    print("notebook controlled sweep contract passed")
