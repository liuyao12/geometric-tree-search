#!/usr/bin/env python3
"""Contract for the live per-leap morphology passport."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_live_morphology_contract() -> None:
    assert 'buildId: "20260825-145"' in APP
    assert 'app.js?v=20260825-145' in HTML
    for element_id in (
        "leapMorphologyPassport",
        "leapMorphologyState",
        "leapMorphologySpectrum",
        "leapMorphologyMetrics",
        "leapMorphologyBoundary",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "function morphologyTrend" in APP
    assert "function renderLeapMorphology" in APP
    assert "renderLeapMorphology(selected)" in APP
    assert "principalVarianceFractions.forEach" in APP
    for label in (
        "covariance phenotype",
        "structural dimension",
        "radius of gyration",
        "maximum extent",
        "shape anisotropy κ²",
        "coordination exposure",
    ):
        assert f'metric("{label}"' in APP
    assert "surface completing" in APP
    assert "exposure increasing" in APP
    assert "anisotropy increasing" in APP
    assert "compactifying" in APP
    assert "shape-preserving expansion" in APP
    assert "not physical surface area" in APP
    assert "growth rate" in APP
    assert ".leap-morphology-passport" in CSS
    assert ".leap-morphology-spectrum" in CSS
    assert ".leap-morphology-metrics" in CSS
    assert "Build 125" in README
    assert "without adding\nnon-atomic glyphs" in README


if __name__ == "__main__":
    test_live_morphology_contract()
    print("live morphology contract passed")
