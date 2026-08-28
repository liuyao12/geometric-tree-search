#!/usr/bin/env python3
"""Contract for the post-decision spatial growth-event and branch microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps/iqc-growth-live"
APP = (APP_DIR / "app.js").read_text()
HTML = (APP_DIR / "index.html").read_text()
CSS = (APP_DIR / "style.css").read_text()
README = (APP_DIR / "README.md").read_text()


def test_growth_event_map_and_branch_microscope_are_read_only_diagnostics() -> None:
    for element_id in (
        "growthMechanismSection",
        "growthMechanismState",
        "growthMechanismProjection",
        "growthMechanismCanvas",
        "growthMechanismDetailState",
        "growthMechanismDetail",
        "growthMechanismLocalState",
        "growthMechanismLocalCanvas",
        "growthMechanismPhysicsState",
        "growthMechanismPhysicsTerms",
        "growthMechanismPhysicsGates",
        "growthMechanismPhysicsContribution",
        "growthMechanismPhysicsInfluence",
        "growthMechanismPhysicsSensitivity",
        "growthMechanismPhysicsBoundary",
        "growthMechanismPrevious",
        "growthMechanismNext",
        "growthMechanismPin",
        "growthMechanismNearestOpposite",
        "growthMechanismComparisonClear",
        "growthMechanismComparisonState",
        "growthMechanismComparison",
        "growthMechanismLedger",
        "growthMechanismBoundary",
        "growthUncertaintyState",
        "growthUncertaintyBudget",
    ):
        assert f'id="{element_id}"' in HTML

    assert "function growthEventNeighborhood(candidate, evaluation)" in APP
    assert "function classifyGrowthEvent(candidate, evaluation)" in APP
    assert '/duplicate|redundant|no novel/.test(reason)' in APP
    assert 'else if (!evaluation.accepted) phenotype = "prune"' in APP
    assert "function prepareGrowthMechanismDiagnostic(candidate, evaluation)" in APP
    assert "function recordGrowthMechanismEvent(candidate, evaluation, accepted, depth, frozenDiagnostic = null)" in APP
    assert "function growthMechanismAudit()" in APP
    assert "function drawGrowthMechanismMap()" in APP
    assert "function renderGrowthMechanismAudit()" in APP
    assert "function growthDecisionUncertainty(candidate, evaluation, nearbyRoleCounts, executePerturbation)" in APP
    assert "function candidatePosePerturbationAudit(candidate)" in APP
    assert "function growthEventLocalGeometry(candidate, evaluation, neighborhoodReach)" in APP
    assert "function drawGrowthMechanismLocalGeometry(event = selectedGrowthMechanismEvent())" in APP
    assert "function renderGrowthUncertaintyBudget()" in APP
    assert "recordGrowthMechanismEvent(candidate, snapshotEvaluation, false" in APP
    assert "recordGrowthMechanismEvent(candidate, evaluation, true, parentDepth + 1," in APP
    assert "spatialGrowthEventAudit: growthMechanismAudit()" in APP
    assert "events: growthMechanismEvents.map(({ position, localGeometry, ...event })" in APP
    assert "eventsObserved" in APP
    assert "maximumStoredEvents: 96" in APP
    assert "coordinatesEmbedded: false" in APP
    assert "localGeometryDisplayCoordinatesEmbedded: false" in APP
    assert "localGeometryDisplayOnly: true" in APP
    assert "localGeometryDisplayTargetUsed:" in APP
    assert "interactiveSelectionSerialized: false" in APP
    assert "interactiveSelectionUsedForSearch: false" in APP
    assert "interactiveComparisonSerialized: false" in APP
    assert "matchedActionPairUsedForSearch: false" in APP
    assert "comparisonDescriptorOutcomeIncluded: false" in APP
    assert "comparisonDescriptorGateSignalsIncluded: false" in APP
    assert "comparisonDescriptorAbsolutePositionIncluded: false" in APP
    assert "comparisonDescriptorProperRotationInvariant: true" in APP
    assert "usedForCandidateEnumeration: false" in APP
    assert "usedForAdmission: false" in APP
    assert "usedForBranchRanking: activeMicrostructureCouplingWeight() > 0" in APP
    assert "defectLabelsAssigned: false" in APP
    assert "physicalMechanismAssigned: false" in APP
    assert "formationEnergyInferred: false" in APP
    assert "kineticsInferred: false" in APP
    assert "post-decision" in APP
    assert "measurementFloorActive" in APP
    assert "minimumContactClearanceAngstrom" in APP
    assert "maximumOverlapResidualAngstrom" in APP
    assert "markingMargin" in APP
    assert "markingHoldoutLoss" in APP
    assert "perturbationEnsembleExecutedForThisAction: true" in APP
    assert "perturbationAuditTargetUsed: false" in APP
    assert "candidateSelectionTargetUsed: !reconstructionCertified" in APP
    assert "const MAXIMUM_POSE_AUDITS_PER_LEAP = 64" in APP
    assert "maximumPoseAuditsPerLeap: MAXIMUM_POSE_AUDITS_PER_LEAP" in APP
    assert "deterministic per-leap audit cap reached" in APP
    assert "const diagnosticOptions = { refinePose: false, recordWork: false, targetAware: false, enforceMarking: false }" in APP
    assert "perturbationAgreementFraction" in APP
    assert "decisions pose-audited" in APP
    assert "trials agree" in APP
    assert "confidence unclaimed" in APP
    assert "statisticalConfidenceClaimed: false" in APP
    assert "function selectedGrowthMechanismEvent()" in APP
    assert 'function selectGrowthMechanismEvent(eventId, synchronizeHistory = true, comparisonMode = "manual")' in APP
    assert "function growthMechanismGateSummary(event)" in APP
    assert "function renderGrowthMechanismDetail()" in APP
    assert "function growthActionComparisonDescriptor(event)" in APP
    assert "function growthActionDescriptorDistance(first, second)" in APP
    assert "function nearestOppositeGrowthAction(reference)" in APP
    assert "function renderGrowthMechanismComparison()" in APP
    assert "function freezeGrowthActionPhysicsFingerprint(entry)" in APP
    assert "function rankGrowthActionPhysicsFingerprint(entry, rank, candidateCount, leaderScore)" in APP
    assert "function freezeGrowthActionRankSensitivity(ranked)" in APP
    assert "function renderGrowthMechanismPhysicsAttribution()" in APP
    assert "growth-action physics fingerprint does not reconcile with the ranking score" in APP
    assert "candidate.growthPhysicsAttribution = freezeGrowthActionPhysicsFingerprint(entry)" in APP
    assert "rankGrowthActionPhysicsFingerprint(entry," in APP
    assert "freezeGrowthActionRankSensitivity(ranked)" in APP
    assert "physicsAttribution: candidate.growthPhysicsAttribution" in APP
    assert "physicsAttributionSerialized: true" in APP
    assert "physicsAttributionCoordinatesEmbedded: false" in APP
    assert "physicsAttributionTargetUsedForCandidateSet: false" in APP
    assert "physicsAttributionUsedForSearch: false" in APP
    assert "underlyingSoftTermsUsedForBranchRanking: true" in APP
    assert "physicsHardGatesSeparatedFromSoftTerms: true" in APP
    assert "physicsRankSensitivitySerialized: true" in APP
    assert "physicsRankSensitivityCandidateSetChanged: false" in APP
    assert "physicsRankSensitivityHardAdmissionChanged: false" in APP
    assert "physicsRankSensitivityExecuted: false" in APP
    assert "physicsRankSensitivityCausalEffectIdentified: false" in APP
    assert "set exactly one active physical-surrogate contribution to zero for every candidate" in APP
    assert "causalEffectIdentified: false" in APP
    assert 'growthMechanismPhysicsContribution.addEventListener("click"' in APP
    assert 'growthMechanismPhysicsInfluence.addEventListener("click"' in APP
    assert "physicalEnergyInferred: false" in APP
    assert "physicalRateInferred: false" in APP
    assert "physicalTimeInferred: false" in APP
    assert 'selectedLeapIndex = retainedIndex' in APP
    assert "the structural-history panels follow its retained leap without rewinding the live atoms" in APP
    assert "This forensic view never changes rank, admission, or geometry." in APP
    assert 'growthMechanismCanvas.addEventListener("click"' in APP
    assert 'growthMechanismCanvas.addEventListener("keydown"' in APP
    assert 'event.key === "Home"' in APP
    assert "growthMechanismScreenPoints.push" in APP
    assert "coordinatesRelativeToCandidateCenter: true" in APP
    assert 'coordinateUnit: "angstrom"' in APP
    assert "maximumContextSites: 48" in APP
    assert "contextTruncated: contextById.size > 48" in APP
    assert "usedForCandidateEnumeration: false" in APP[APP.index("function growthEventLocalGeometry("):
                                                         APP.index("function candidatePosePerturbationAudit(")]
    assert "usedForAdmission: false" in APP[APP.index("function growthEventLocalGeometry("):
                                             APP.index("function candidatePosePerturbationAudit(")]
    assert "usedForBranchRanking: false" in APP[APP.index("function growthEventLocalGeometry("):
                                                 APP.index("function candidatePosePerturbationAudit(")]
    assert "drawGrowthMechanismLocalGeometry();" in APP
    assert "const hasDistinguishedCenter" in APP
    assert "hasDistinguishedCenter && outerIndices.length >= 3" in APP
    assert "? outerIndices : geometry.candidateSites.map" in APP
    assert "site.offsetAngstrom[depth] * .28" in APP
    assert "with depth cue" in APP
    descriptor = APP[APP.index("function growthActionComparisonDescriptor("):
                     APP.index("function growthActionDescriptorDistance(")]
    for forbidden in ("event.accepted", "event.gateSignals", "event.reason", "event.position"):
        assert forbidden not in descriptor
    comparison = APP[APP.index("function renderGrowthMechanismComparison("):
                     APP.index("function renderGrowthMechanismDetail(")]
    for forbidden in ("materializeCandidate(", "evaluateCandidate(", "performOffLatticeEvent",
                      "atoms =", "placedClusters ="):
        assert forbidden not in comparison
    attribution = APP[APP.index("function renderGrowthMechanismPhysicsAttribution("):
                      APP.index("function renderGrowthMechanismComparison(")]
    for forbidden in ("materializeCandidate(", "evaluateCandidate(", "performOffLatticeEvent",
                      "atoms =", "placedClusters ="):
        assert forbidden not in attribution
    assert "distance excludes fate, gate signals, reason, action ID, and absolute position" in APP
    assert "descriptive matched pair from a capped, correlated action ledger" in APP
    selector = APP[APP.index("function selectGrowthMechanismEvent("):
                   APP.index("function growthMechanismGateSummary(")]
    for forbidden in ("atoms =", "placedClusters =", "materializeCandidate(",
                      "evaluateCandidate(", "performOffLatticeEvent"):
        assert forbidden not in selector
    accepted_record = "recordGrowthMechanismEvent(candidate, evaluation, true, parentDepth + 1,"
    accepted_materialize = "const placement = materializeCandidate(candidate, evaluation, leapCreationContext)"
    assert APP.index(accepted_record) < APP.index(accepted_materialize, APP.index(accepted_record))

    assert ".growth-mechanism-section" in CSS
    assert ".growth-mechanism-ledger" in CSS
    assert ".growth-decision-microscope" in CSS
    assert ".growth-decision-grid" in CSS
    assert ".growth-local-geometry" in CSS
    assert ".growth-local-legend" in CSS
    assert ".growth-action-comparison" in CSS
    assert ".growth-physics-attribution" in CSS
    assert ".growth-physics-term.positive" in CSS
    assert ".growth-physics-gates" in CSS
    assert ".growth-physics-sensitivity" in CSS
    assert ".growth-uncertainty-budget" in CSS
    assert "spatial growth-event audit" in README
    assert "not automatic defect identities" in README
    assert "uncertainty budget" in README
    assert "bounded pose ensemble" in README
    assert "64 encountered decisions" in README
    assert "do not increment search-work counters" in README
    assert "not a posterior probability" in README


if __name__ == "__main__":
    test_growth_event_map_and_branch_microscope_are_read_only_diagnostics()
    print("spatial growth-event and branch-microscope contract: passed")
