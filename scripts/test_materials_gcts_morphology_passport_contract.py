#!/usr/bin/env python3
"""Contract for per-leap morphology passports and notebook comparison."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_morphology_passport_contract() -> None:
    assert 'buildId: "20260825-137"' in APP
    assert 'app.js?v=20260825-137' in HTML
    assert 'id="notebookTrajectoryObservable"' in HTML
    for observable in ("atoms", "radius", "extent", "anisotropy", "exposure", "dimension"):
        assert f'value="{observable}"' in HTML
    assert "function structuralMorphologySnapshot" in APP
    assert "inferPointSetDimension(source)" in APP
    assert "coloredCoordinationDeficit" in APP
    assert "principalVarianceFractions" in APP
    assert "principalVarianceAngstromSquared" in APP
    assert "radiusOfGyrationAngstrom" in APP
    assert "maximumExtentAngstrom" in APP
    assert "relativeShapeAnisotropy" in APP
    assert "coordinationDeficit" in APP
    assert 'coordinateFrameUsed: false, targetUsed: false' in APP
    assert "physicalSurfaceAreaInferred: false" in APP
    assert "equilibriumHabitInferred: false" in APP
    assert "morphology: structuralMorphologySnapshot()" in APP
    assert "morphology: leap.after?.morphology || null" in APP
    assert "NOTEBOOK_TRAJECTORY_OBSERVABLES" in APP
    assert "morphologyAvailable" in APP
    assert "Existing run upgraded with its coordinate-free morphology passport." in APP
    assert ".notebook-trajectory-observable" in CSS
    assert "morphology passport" in README.lower()
    assert "not an equilibrium crystal habit" in README


if __name__ == "__main__":
    test_morphology_passport_contract()
    print("morphology passport contract passed")
