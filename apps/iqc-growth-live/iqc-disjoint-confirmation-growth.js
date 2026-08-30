const SPECIES = new Set(["Al", "Cu", "Fe"]);

function validateSite(site) {
  return Array.isArray(site) && site.length === 4 && SPECIES.has(site[0])
    && site.slice(1).every(Number.isFinite);
}

export function validateIqcDisjointConfirmationArtifact(artifact) {
  const valid = artifact?.id === "iqc-sealed-disjoint-frontier-confirmation-v1"
    && artifact.seedAtomCount === 473
    && artifact.seedSites?.length === artifact.seedAtomCount
    && artifact.seedSites.every(validateSite)
    && artifact.selectedTerminalIndex === 101
    && artifact.selectedTerminalSiteCount === 3
    && artifact.selectedActionSites?.length === artifact.selectedTerminalSiteCount
    && artifact.selectedActionSites.every(validateSite)
    && artifact.terminalCount === 128
    && artifact.exactTerminalCountPosthoc === 90
    && artifact.targetDomainDisjoint === true
    && artifact.candidatesFrozenBeforeTarget === true
    && artifact.targetUsedForFitCandidateOrRanking === false
    && artifact.targetOpenCount === 1
    && artifact.firstFusionTopOneExact === true
    && artifact.stationaryOrExponentialClaimed === false
    && artifact.secondBlock?.terminalCount === 128
    && artifact.secondBlock?.exactTerminalCountPosthoc === 62
    && artifact.secondBlock?.scalarFirstExactRank === 13
    && artifact.secondBlock?.fusionFirstExactRank === 16
    && artifact.secondBlock?.fusionTopOneExact === false
    && artifact.secondBlock?.portfolioSuppliesExact === false
    && artifact.secondBlock?.completeTreeSuppliesExact === true
    && artifact.secondBlock?.sixActionAutonomousGatePassed === false
    && artifact.secondBlock?.stationaryOrExponentialClaimed === false;
  if (!valid) throw new Error("Invalid sealed IQC disjoint-confirmation artifact");
  return artifact;
}

function traceSite([species, x, y, z]) {
  return Object.freeze([species, Object.freeze([x, y, z])]);
}

export function executeIqcDisjointConfirmation(artifact) {
  validateIqcDisjointConfirmationArtifact(artifact);
  return Object.freeze({
    caseId: artifact.id,
    artifactDigest: artifact.coordinateSpeciesSha256,
    protocolDigest: artifact.protocolDigest,
    candidateReceiptDigest: artifact.candidateReceiptDigest,
    candidateSetDigest: artifact.candidateSetDigest,
    seedRadius: artifact.seedRadius,
    firstTargetRadius: artifact.firstTargetRadius,
    seedSites: Object.freeze(artifact.seedSites.map(traceSite)),
    seedAtomCount: artifact.seedAtomCount,
    targetAtomCountPosthoc: artifact.targetAtomCountPosthoc,
    novelTargetAtomCountPosthoc: artifact.novelTargetAtomCountPosthoc,
    targetDomainDisjoint: artifact.targetDomainDisjoint,
    candidatesFrozenBeforeTarget: artifact.candidatesFrozenBeforeTarget,
    targetUsed: artifact.targetUsedForFitCandidateOrRanking,
    targetOpenCountPosthoc: artifact.targetOpenCount,
    waves: Object.freeze([
      Object.freeze({
        wave: 1,
        candidateTerminals: artifact.terminalCount,
        exactTerminalsPosthoc: artifact.exactTerminalCountPosthoc,
        selectedTerminalIndex: artifact.selectedTerminalIndex,
        selectedRank: 1,
        selectedExactPosthoc: artifact.firstFusionTopOneExact,
        emittedSites: Object.freeze(artifact.selectedActionSites.map(traceSite)),
        candidateDigest: artifact.candidateSetDigest,
        acceptedActions: 3,
        acceptedSites: artifact.selectedTerminalSiteCount,
      }),
      Object.freeze({
        wave: 2,
        candidateTerminals: artifact.secondBlock.terminalCount,
        exactTerminalsPosthoc: artifact.secondBlock.exactTerminalCountPosthoc,
        scalarFirstExactRank: artifact.secondBlock.scalarFirstExactRank,
        fusionFirstExactRank: artifact.secondBlock.fusionFirstExactRank,
        selectedExactPosthoc: artifact.secondBlock.fusionTopOneExact,
        acceptedActions: 0,
        acceptedSites: 0,
        emittedSites: Object.freeze([]),
        evidenceBoundary: artifact.secondBlock.honestStatus,
      }),
    ]),
    selectedFirstActionExactPosthoc: artifact.firstFusionTopOneExact,
    secondBlockCompleteTreeSuppliesExact: artifact.secondBlock.completeTreeSuppliesExact,
    secondBlockFrozenSelectionPassed: artifact.secondBlock.fusionTopOneExact,
    autonomousContinuationCertified: artifact.secondBlock.sixActionAutonomousGatePassed,
    stationaryOrExponentialClaimed: artifact.stationaryOrExponentialClaimed,
    claimBoundary: "One pre-target-selected three-site terminal is exactly confirmed at a fresh spatially disjoint nucleus. The next complete tree contains exact terminals, but the frozen selector does not choose one; no sustained, stationary, or exponential continuation is certified.",
  });
}
