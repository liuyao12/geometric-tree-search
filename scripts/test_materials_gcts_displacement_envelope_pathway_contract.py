from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CORE = (ROOT / "apps/iqc-growth-live/interstitial-clearance.js").read_text()


def test_displacement_envelope_pathway_contract():
    assert 'id="voidDisplacementModel"' in HTML
    assert '+ 1σ ADP envelope' in HTML and '+ 3σ ADP envelope' in HTML
    assert 'currentDisplacementTensorsAngstrom2' in APP
    assert 'referenceDisplacementTensorsAngstrom2' in APP
    assert 'selectedVoidDisplacementSigma' in APP
    assert 'displacementClearanceKey' in APP
    assert 'clearanceModelsAtPoint' in CORE
    assert 'clearanceModelsAlongSegment' in CORE
    assert 'directional k sqrt(n^T U n)' in CORE
    assert 'displacementEnvelopeIsTrajectory: false' in CORE
    assert 'displacementEnvelopeIsProbabilityOrConfidenceRegion: false' in CORE
