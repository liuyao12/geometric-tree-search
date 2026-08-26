#!/usr/bin/env python3
"""Contract for finite structural mass-radius scaling."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
PHASE = (ROOT / "apps/iqc-growth-live/phase-evidence.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_mass_radius_scaling_contract() -> None:
    assert 'buildId: "20260825-133"' in APP
    assert 'app.js?v=20260825-133' in HTML
    assert 'id="leapMorphologyScaling"' in HTML
    assert '$("leapMorphologyScaling")' in APP
    assert "export function finiteMassRadiusScaling" in PHASE
    assert "minimumStates = 3" in PHASE
    assert "minimumRadiusRatio = 1.25" in PHASE
    assert "minimumRSquared = .8" in PHASE
    assert "asymptoticFractalDimensionInferred: false" in PHASE
    assert "physicalTimeUsed: false" in PHASE
    assert "kineticsInferred: false" in PHASE
    assert "coordinatesUsed: false" in PHASE
    assert "function structuralMorphologySeries" in APP
    assert "function structuralMassRadiusScaling" in APP
    assert "function receiptMassRadiusScaling" in APP
    assert "structuralMassRadiusScaling: receiptMassRadiusScaling()" in APP
    assert "function notebookMassRadiusScaling" in APP
    assert "massRadiusScaling: notebookMassRadiusScaling(trajectoryPoints)" in APP
    assert "finite mass–radius Dₘ" in APP
    assert "not fractal dimension or kinetics" in APP
    assert "retainedWindowTruncated" in APP
    assert ".leap-morphology-scaling" in CSS
    assert "Build 126" in README
    assert "not asserted to be an asymptotic fractal dimension" in README


if __name__ == "__main__":
    test_mass_radius_scaling_contract()
    print("mass-radius scaling contract passed")
