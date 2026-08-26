from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_map_uses_exact_bounded_local_coordination_geometry():
    assert "function currentBondValenceSpatialField(maximumCenters = 320)" in APP
    assert "radiallyStratifiedIndices(atoms, eligibleIndices, maximumCenters)" in APP
    assert "nearbyAtoms(atom.p, cutoffSceneUnits)" in APP
    assert "bondValenceSums([atom, ...neighbors].map(toPhysical))" in APP
    assert 'finiteObservationNoPeriodicImages: true' in APP
    assert 'elementColorsPreserved: true' in APP


def test_map_exposes_scalar_halos_and_directional_resultants():
    assert 'id="bondValenceMapSelect"' in HTML
    assert 'id="bondValenceMapState"' in HTML
    assert 'id="bondValenceMapExtremes"' in HTML
    assert 'value="scalar"' in HTML
    assert 'value="vector"' in HTML
    assert 'bondValenceMapMode === "scalar" ? record.scalarResidual : record.vectorMagnitude' in APP
    assert "new THREE.Vector3(...record.vectorSum)" in APP
    assert "function renderBondValenceMapExtremes(field)" in APP
    assert "controls.target.copy(record.atom.p)" in APP
    assert ".bond-valence-map-legend i.under" in CSS
    assert ".bond-valence-map-legend i.balanced" in CSS
    assert ".bond-valence-map-legend i.over" in CSS
    assert ".bond-valence-map-extremes button.active" in CSS


def test_map_is_display_only_and_receipted():
    assert "function bondValenceSpatialFieldReceipt()" in APP
    assert "spatialDefectMap: bondValenceSpatialFieldReceipt()" in APP
    assert 'displayOnly: true, vectorArrowsAreForces: false, energyInferred: false' in APP
    assert 'candidateRankingChanged: false, candidateGeometryChanged: false' in APP
    assert 'hardAdmissionChanged: false, targetUsed: false, physicalTimeIntegrated: false' in APP
    assert 'bondValenceMapSelect.addEventListener("change"' in APP
