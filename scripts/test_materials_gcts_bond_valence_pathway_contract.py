from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()


def test_structural_state_uses_bounded_exact_neighbor_halos():
    assert "function structuralBondValenceSnapshot(maximumCenters = 96)" in APP
    assert "radiallyStratifiedIndices(atoms, eligibleIndices, maximumCenters)" in APP
    assert "nearbyAtoms(center.p, cutoffSceneUnits)" in APP
    assert "bondValenceStateSummary(neighborhoods)" in APP
    assert 'finiteObservationNoPeriodicImages: true' in APP
    assert 'candidateRankingChanged: false' in APP
    assert 'analysisOnly: true, targetUsed: false' in APP


def test_structural_leaps_retain_scalar_and_vector_state():
    assert APP.count("bondValenceState: structuralBondValenceSnapshot()") >= 6
    assert "sampledRmsValenceMismatch" in APP
    assert "sampledMeanVectorMagnitude" in APP
    assert "bondValenceStructuralPathway: bondValenceStructuralPathwayReceipt()" in APP
    assert 'alignment: "discrete GCTS structural leap; not physical time"' in APP
    assert 'sphericalIonHypothesisOnly: true, anisotropyCanBePhysical: true' in APP


def test_pathway_is_interactive_and_visually_separate_from_candidate_scores():
    assert 'id="bondValencePortrait"' in HTML
    assert 'id="bondValencePath"' in HTML
    assert 'id="bondValencePathState"' in HTML
    assert 'id="bondValencePathReadout"' in HTML
    assert "function renderBondValenceStructuralPathway()" in APP
    assert 'xLabel.textContent = "sampled RMS valence mismatch →"' in APP
    assert 'yLabel.textContent = "mean vector resultant →"' in APP
    assert 'point.addEventListener("click", select)' in APP
    assert ".bond-valence-path .history-line" in CSS
    assert ".bond-valence-path .history-point.selected" in CSS
