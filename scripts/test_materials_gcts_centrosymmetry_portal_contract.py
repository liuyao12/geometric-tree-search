from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/centrosymmetry-geometry.js").read_text()


def test_centrosymmetry_microscope_is_public_and_explicitly_bounded():
    assert 'buildId: "20260826-166"' in APP
    assert 'app.js?v=20260831-403' in HTML
    assert 'value="centrosymmetry"' in HTML
    assert 'id="centrosymmetryNeighborSelect"' in HTML
    assert 'id="centrosymmetryMapButton"' in HTML
    assert 'inferCentrosymmetryNeighborCount' in APP
    assert 'localCentrosymmetry' in APP
    assert 'selectedCentrosymmetryDetail' in APP
    assert 'currentCentrosymmetryField' in APP
    assert 'not a defect identity or energy' in APP
    assert '10.1103/PhysRevB.58.11085' in MODULE
    assert 'minimum-weight perfect pairing' in MODULE
    assert 'uniformScaleInvariant: true' in MODULE
