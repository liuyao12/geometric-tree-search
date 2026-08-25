"""Static contract for fixed-topology snapshot ensembles in the browser lab."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_trajectory_ensemble_keeps_evidence_and_growth_domains_separate() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    io = (APP / "structure-io.js").read_text(encoding="utf-8")
    envelopes = (APP / "colored-distance-envelopes.js").read_text(encoding="utf-8")
    uncertainty = (APP / "ensemble-geometry-uncertainty.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")

    assert 'id="ensembleControls"' in html
    assert 'id="ensembleFrameSelect"' in html
    assert 'id="ensembleEvidenceSelect"' in html
    assert 'id="loadEnsembleFixtureButton"' in html
    assert 'value="all" selected' in html
    assert 'value="selected"' in html
    assert 'app.js?v=20260825-97' in html

    assert "function parseXyzFrame" in io
    assert "function jsonFrameRecord" in io
    assert "trajectoryTopologyConsistent" in io
    assert "changes atom count, order, species, occupancy, or formal charge" in io
    assert "maximumFrames = options.maximumFrames || 64" in io
    assert "maximumAtomPresentations = options.maximumAtomPresentations || 24000" in io

    assert "learnColoredDistanceEnvelopesEnsemble" in envelopes
    assert "learnColoredCoordinationEnvelopesEnsemble" in envelopes
    assert "learnColoredAngularEnvelopesEnsemble" in envelopes
    assert "frames.forEach(({ species, distance })" in envelopes
    assert "frames.forEach(({ species, displacement }, frameIndex)" in envelopes
    assert "learnLocalPairDistanceUncertaintyEnsemble" in uncertainty
    assert "sampleStandardDeviation" in uncertainty
    assert "crossFramePairsConstructed: false" in uncertainty
    assert "temporalOrderingUsed: false" in uncertainty

    assert "function currentImportedFrame()" in source
    assert "function deterministicSnapshotEnsemble(structure)" in source
    assert "function referenceEvidenceFrames(source)" in source
    assert "function learnReferenceEnsemblePairUncertainty()" in source
    assert "ensembleEvidenceMode !== \"all\"" in source
    assert "const commonSceneScale = referenceSpacing / referenceSpacingA" in source
    assert "return makeImportedFrameReference();" in source
    assert "Frame ${importedFrameIndex + 1} alone supplies the cluster cover, grammar, and growth seed." in source

    assert "framesUsedForDistanceCoordinationAngleEnvelopes" in source
    assert "framesUsedForClusterCover: 1" in source
    assert "framesUsedForPortGrammarAndMarking: 1" in source
    assert "framesUsedForGrowthSeed: 1" in source
    assert "crossFrameAtomPairsConstructed: false" in source
    assert "temporalOrderingUsed: false" in source
    assert "velocitiesUsed: false" in source
    assert "forcesUsed: false" in source
    assert "integrationTimeStepUsed: false" in source
    assert "independentSampleCountClaimed: false" in source
    assert "upperPairDistanceSigmaAngstrom" in source
    assert "trajectoryIntegrated: false" in source
    assert "kineticsInferredFromSnapshotOrder: false" in source

    assert "frames are never concatenated into one point cloud" in readme
    assert "ensemble-informed structural geometry" in readme
    assert "Reactions, changing atom identity" in readme


if __name__ == "__main__":
    test_trajectory_ensemble_keeps_evidence_and_growth_domains_separate()
    print("trajectory ensemble integration contract: passed")
