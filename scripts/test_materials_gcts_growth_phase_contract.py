"""Source contract for growth-only, auditable emergent phase inference."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_phase_inference_is_posthoc_traced_and_receipted() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    html = (APP / "index.html").read_text(encoding="utf-8")
    css = (APP / "style.css").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    assert "const PHASE_CLASSIFICATION_MINIMUM_ATOMS = 32" in source
    assert "const PHASE_CLASSIFICATION_THRESHOLD = .58" in source
    assert 'if (pipelineStage < 4 || currentMaterial().growthWithheld) return {' in source
    assert 'currentMaterial().growthWithheld ? "occupational realization unresolved" : "classification begins after growth"' in source
    assert "posthocOnly: true, usedAsGrowthInput: false" in source
    assert "independentPhaseDetermination: false" in source
    assert 'structure = crystalPrototypeResolved ? bestCrystal.material.name : "periodic crystal · prototype unresolved"' in source
    assert 'symmetry = crystalPrototypeResolved ? bestCrystal.material.symmetry : "translation group detected · point group unresolved"' in source
    assert 'accepted && bestPrototypeResolved && best.material.order === "crystal"' in source
    assert 'accepted && bestPrototypeResolved && best.material.order === "quasicrystal"' in source
    assert 'accepted && bestPrototypeResolved && best.material.order === "amorphous"' in source

    assert "function recordLiveOrder(inference)" in source
    assert "function drawPhaseTrajectory()" in source
    assert 'from "./phase-evidence.js?v=20260824-1"' in source
    assert "centeredStructuralWindow(availableSource, matchedAtomCount)" in source
    assert "inferPointSetDimension(source)" in source
    assert "phaseComparisonRadius(source.length, dimensionAudit.dimension)" in source
    assert "matchedPrototypeStats(prototype, source.length, comparisonRadius)" in source
    assert "independentMatches = matches.filter((match) => match.id !== scenarioSelect.value)" in source
    assert "liveOrderHistory = []" in source
    assert "if (previous?.historyKey === inference.historyKey) return" in source
    assert "if (liveOrderHistory.length > 96)" in source
    assert "phaseTrajectoryColor" in source

    assert 'id="phaseTrajectoryCanvas"' in html
    assert 'id="phaseWindowValue"' in html
    assert 'id="phaseMarginValue"' in html
    assert 'id="phaseIndependentValue"' in html
    assert 'id="phaseClosureValue"' in html
    assert "posthoc interpretation" in html
    assert "confidence trajectory" in html
    assert ".phase-trajectory" in css
    assert ".phase-evidence-grid" in css

    assert "function receiptEmergentClassification()" in source
    assert "emergentClassification: receiptEmergentClassification()" in source
    assert 'stageGate: currentMaterial().growthWithheld ? "material growth unavailable for average occupancy" : "material growth only"' in source
    assert "usedForCandidateAdmission: false" in source
    assert "usedForBranchRanking: false" in source
    assert "selectedFixturePresentInPrototypeLibrary" in source
    assert "atomCountMatchedAcrossPrototypeWindows: true" in source
    assert "intrinsicDimensionInferredFromPositionCovariance: true" in source
    assert "curatedIntrinsicDimensionUsed: false" in source
    assert "localPlanarityRatio: dimensionAudit.localPlanarityRatio" in source
    assert "dimensionInferenceBasis: dimensionAudit.basis" in source
    assert "leaveSelectedFixtureOut: {" in source
    assert "prototypeComparisonWeights: { rdf: .30, coordination: .58, geometricPowderStructureFactor: .20 }" in source
    assert "trajectory: liveOrderHistory.map" in source
    assert "coordinatesEmbedded: false" in source

    assert "confidence against the live atom count" in readme
    assert "prototype-library self-reference flag" in readme
    assert "a tied or under-supported numerical leader is never promoted" in normalized_readme
    assert "truncates every prototype to the same atom count" in normalized_readme
    assert "curated material dimension is not consulted" in normalized_readme
    assert 'style.css?v=20260825-46' in html
    assert 'app.js?v=20260825-103' in html


if __name__ == "__main__":
    test_phase_inference_is_posthoc_traced_and_receipted()
    print("growth-only emergent phase contract: passed")
