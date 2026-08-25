"""Source contract for the live material- and stage-specific scale passport."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"


def test_scale_passport_maps_evidence_to_claim_boundaries() -> None:
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    source = (APP_DIR / "app.js").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")
    readme = (APP_DIR / "README.md").read_text(encoding="utf-8")

    assert 'aria-label="Live multiscale geometry passport"' in html
    for element_id in ("scalePassportState", "scalePassport", "scalePassportDetail"):
        assert f'id="{element_id}"' in html

    assert "function clusterDiameterRangeAngstrom()" in source
    assert "function liveScalePassportRecords()" in source
    assert "function renderScalePassport()" in source
    for scale_id in ("contacts", "clusters", "marking", "continuation", "kinetics"):
        assert f'id: "{scale_id}"' in source
    for field in ("observed evidence", "geometric encoding", "role in search", "claim boundary"):
        assert field in source
    assert "renderScalePassport();" in source
    assert "activeMeasurementConditions()" in source
    assert "retained as provenance only" in source
    assert "No temperature-dependent free energy" in source

    assert "multiscalePassport: {" in source
    assert "coordinateDataEmbedded: false" in source
    assert "kineticsModeled: false" in source
    assert "geometricEncoding: record.encoding" in source
    assert "claimBoundary: record.boundary" in source

    assert ".scale-passport" in css
    assert ".scale-passport-detail" in css
    assert "multiscale geometry passport" in readme
    assert "never promoted into an uncalibrated simulation control" in readme


if __name__ == "__main__":
    test_scale_passport_maps_evidence_to_claim_boundaries()
    print("live multiscale geometry passport contract: passed")
