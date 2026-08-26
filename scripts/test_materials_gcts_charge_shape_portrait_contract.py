#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_charge_shape_portrait_contract():
    assert 'buildId: "20260826-162"' in APP
    assert 'app.js?v=20260826-162' in HTML
    assert 'style.css?v=20260826-69' in HTML
    for element_id in ("chargeShapePortraitState", "chargeShapePortrait", "chargeShapePortraitDetail"):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    assert "function buildChargeShapePortrait" in APP
    assert "function renderChargeShapePortrait" in APP
    assert "function previewChargeShapeCandidate" in APP
    assert "candidateSetChanged: false" in APP
    assert "suppliedFormalChargeOnly: true" in APP
    assert "targetUsed: false" in APP
    assert "globalChargeShapePortrait" in APP
    assert "chargeShapeCandidateKey" in APP
    assert ".charge-shape-portrait-card" in CSS
    assert ".charge-shape-portrait .candidate:hover" in CSS
    assert "not energy, electric field, polarization" in APP
    assert "Build 156" in README


if __name__ == "__main__":
    test_charge_shape_portrait_contract()
    print("charge-shape portrait contract passed")
