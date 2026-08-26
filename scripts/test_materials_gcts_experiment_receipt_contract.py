"""Source contract for stage-aware, coordinate-free experiment receipts."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"


def test_experiment_receipt_is_reproducible_and_claim_bounded() -> None:
    source = (APP_DIR / "app.js").read_text(encoding="utf-8")
    html = (APP_DIR / "index.html").read_text(encoding="utf-8")
    css = (APP_DIR / "style.css").read_text(encoding="utf-8")

    assert 'schema: "gcts-materials-growth-receipt-v1"' in source
    assert "async function buildExperimentReceipt()" in source
    assert "async function structureDigest(source, coordinateSpace)" in source
    assert 'crypto.subtle.digest("SHA-256"' in source
    assert "delete experimentState.generatedAt" in source
    assert "receipt.experimentStateSha256" in source
    assert "receipt.receiptSha256" in source

    for section in ("input", "pipeline", "geometry", "cover", "marking", "search", "evidenceBoundary"):
        assert f"    {section}:" in source

    assert "coordinatesEmbedded: false" in source
    assert "targetCoordinatesIncluded: false" in source
    assert "physicalPotentialUsed: false" in source
    assert "physicalElapsedTimeModeled: false" in source
    assert "trajectoryIntegrated: false" in source
    assert "kineticsInferredFromSnapshotOrder: false" in source
    assert "growthRateClaimed: false" in source
    assert "iceProtonOrientationsResolved: trace ? false : null" in source
    assert 'const symbolicRecursiveSystems = new Set(["competition", "graphene", "hbn", "moire"])' in source
    assert 'const stationaryProductionSystems = new Set(["competition"])' in source
    assert 'stationaryProductionCertified: benchmark.status === "pass" && stationaryProductionSystems.has(scenarioId)' in source
    assert "symbolicRecursiveScalingClaimed: symbolicRecursiveScaling" in source
    assert "genericExponentialGctsClaimed: false" in source
    assert "finiteFixedPointContinuation: Boolean(trace?.fixedPoint)" in source
    assert "exactBackendCountParity: iceAnchorTrace.exactBackendCountParity" in source
    assert "emittedAnchorCount: iceAnchorTrace.emittedAnchors.length" in source
    assert "molecularDiscovery: learnedCover.molecularDiscovery || null" in source
    assert "materialLabelUsed: discovery.materialLabelUsed" in source
    assert "expectedFormulaUsed: discovery.expectedFormulaUsed" in source
    assert "irregularMining: learnedCover.irregular || null" in source
    assert "heterogeneousGeometryAudit: receiptMicrostructureAudit()" in source
    assert "gapBoundaryClassesEmitAtoms: false" in (APP_DIR / "microstructure-audit.js").read_text(encoding="utf-8")
    assert "liveCertificate: liveGrowthCertificate()" in source
    assert "structuralLeapCertificates: leapHistory.map" in source
    assert "policySensitivity: {" in source
    assert "candidateCoordinatesEmbedded: false" in source
    assert "candidateSetTargetUsed: snapshot.candidateSetTargetUsed" in source
    assert "rankingTargetUsed: snapshot.rankingTargetUsed" in source
    assert "multiscalePassport: {" in source
    assert "coordinateDataEmbedded: false" in source
    assert "kineticsModeled: false" in source
    assert "physicalTimeModeled: leap.physicalTimeModeled" in source
    assert "dynamicsIntegrated: leap.dynamicsIntegrated" in source
    assert "representationReadout: MARKING_REPRESENTATIONS[activeMarking.config.representation]?.readout" in source
    assert "representationState: activeMarking.representationState || null" in source
    assert "learnedChiralPortClasses: Object.keys(sectionModel.representationState?.chiralPreferences || {}).length" in source
    assert "properSymmetryGaugeCount: poseModel.properSymmetryGaugeCount" in source
    assert "commonProperRotationEquivariant: poseModel.commonProperRotationEquivariant" in source
    assert "improperRotationsQuotiented: poseModel.improperRotationsQuotiented" in source
    assert "recordedMeasurementConditions: recordedConditions ? {" in source
    assert "temperatureSourceTag: recordedConditions.temperature?.sourceTag ?? null" in source
    assert "pressureSourceTag: recordedConditions.pressure?.sourceTag ?? null" in source
    assert "usedAsSimulationControl: false" in source
    assert "synthesisConditionsClaimed: false" in source
    assert "thermodynamicStateReconstructed: false" in source

    assert 'id="downloadReceiptButton"' in html
    assert 'id="copyReceiptButton"' in html
    assert 'id="saveNotebookButton"' in html
    assert 'id="receiptStatus"' in html
    assert 'id="strainValue"' in html
    assert 'id="compositionValue"' in html
    assert 'id="chargeValue"' in html
    assert 'id="surfaceValue"' in html
    assert 'type="text"' not in html[html.index('class="receipt-section"'):html.index('class="legend-section"')]
    assert 'app.js?v=20260825-147' in html
    assert "externalGeometry: receiptExternalGeometry()" in source
    assert 'candidateGeometryChangedByScheduling: false' in source
    assert 'surfaceCompletionRanking: {' in source
    assert 'formalChargeBalanceRanking: {' in source
    assert 'oxidationStatesInferred: false' in source
    assert 'not charge density, Coulomb energy, redox chemistry' in source
    assert 'not bond or surface energy' in source
    assert ".receipt-actions" in css
    assert ".receipt-status" in css


if __name__ == "__main__":
    test_experiment_receipt_is_reproducible_and_claim_bounded()
    print("experiment receipt contract: passed")
