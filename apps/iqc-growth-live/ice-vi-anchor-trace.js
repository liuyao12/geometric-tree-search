function finitePoint(point) {
  return Array.isArray(point) && point.length === 3 && point.every(Number.isFinite);
}

function validSite(site) {
  return Array.isArray(site) && site.length === 2 && site[0] === "O" && finitePoint(site[1]);
}

function siteKey(site) {
  return `${site[0]}:${site[1].map((value) => Math.round(value / 1e-8)).join(":")}`;
}

export function validateIceViAnchorTraceArtifact(artifact) {
  if (artifact?.schema !== "gcts-ice-vi-anchor-trace-v1") {
    throw new Error("Unknown Ice VI anchor-trace schema");
  }
  if (artifact.provenance?.targetUsed || artifact.provenance?.materialLabelUsed
      || artifact.provenance?.expectedFormulaUsed || artifact.provenance?.latticeSiteIndicesUsed
      || artifact.provenance?.energyOrPotentialUsed) {
    throw new Error("Ice VI anchor trace contains forbidden target or material metadata");
  }
  if (!finitePoint(artifact.boundaryCenter) || !(artifact.boundaryRadius > 0)) {
    throw new Error("Ice VI anchor trace has no finite public boundary");
  }
  if (!Array.isArray(artifact.seedSites) || artifact.seedSites.length !== artifact.seedAnchors
      || artifact.seedSites.some((site) => !validSite(site))) {
    throw new Error("Ice VI anchor seed does not match its oxygen-anchor count");
  }
  if (!Array.isArray(artifact.waves) || !artifact.waves.length) {
    throw new Error("Ice VI anchor trace has no executed waves");
  }
  const emitted = [];
  artifact.waves.forEach((wave, index) => {
    if (wave.wave !== index + 1 || wave.candidateAnchors < wave.acceptedAnchors
        || wave.acceptedAnchors !== wave.emittedAnchors.length
        || wave.emittedAnchors.some((site) => !validSite(site))
        || !/^[0-9a-f]{64}$/.test(wave.candidateDigest)) {
      throw new Error(`Invalid Ice VI anchor wave ${index + 1}`);
    }
    emitted.push(...wave.emittedAnchors);
  });
  if (emitted.length !== artifact.emittedAnchors.length
      || emitted.map(siteKey).join("|") !== artifact.emittedAnchors.map(siteKey).join("|")) {
    throw new Error("Ice VI wave emissions do not reproduce the frozen trace");
  }
  const accepted = artifact.waves.map((wave) => wave.acceptedAnchors);
  if (JSON.stringify(accepted) !== JSON.stringify(artifact.expectedCounts)
      || !artifact.exactBackendCountParity) {
    throw new Error("Ice VI browser counts diverge from the sealed backend trace");
  }
  if (!artifact.fixedPoint || artifact.waves.at(-1).acceptedAnchors !== 0
      || artifact.stationaryOrExponentialClaim || !artifact.alternativesAreMutuallyExclusive) {
    throw new Error("Ice VI claim boundary is inconsistent");
  }
  if (artifact.anchorHypothesisCounts.length !== emitted.length
      || artifact.anchorHypothesisCounts.filter((count) => count > 1).length
        !== artifact.unresolvedOrientationHypotheses) {
    throw new Error("Ice VI occupational domains do not match emitted anchors");
  }
  return true;
}

export function executeFrozenIceViAnchorTrace(artifact) {
  validateIceViAnchorTraceArtifact(artifact);
  return {
    caseId: "iceVI",
    artifactDigest: artifact.provenance.traceDigest,
    boundaryCenter: artifact.boundaryCenter.slice(),
    boundaryRadius: artifact.boundaryRadius,
    seedAnchors: artifact.seedAnchors,
    seedSites: artifact.seedSites.map(([species, point]) => [species, point.slice()]),
    waves: artifact.waves.map((wave) => ({
      ...wave,
      emittedAnchors: wave.emittedAnchors.map(([species, point]) => [species, point.slice()]),
    })),
    emittedAnchors: artifact.emittedAnchors.map(([species, point]) => [species, point.slice()]),
    unresolvedOrientationHypotheses: artifact.unresolvedOrientationHypotheses,
    resolvedOrientationHypotheses: artifact.resolvedOrientationHypotheses,
    fixedPoint: artifact.fixedPoint,
    expectedCounts: artifact.expectedCounts.slice(),
    exactBackendCountParity: artifact.exactBackendCountParity,
    targetUsed: false,
    alternativesAreMutuallyExclusive: true,
    stationaryOrExponentialClaim: false,
    portCount: artifact.provenance.frozenPorts,
    conformerTypes: artifact.provenance.conformerTypes,
    moleculeLabel: "D₂O",
    orientationSpecies: "D",
    gapLabel: "O₄",
    selectionRuleLabel: `${artifact.provenance.selectedParentWitnessThreshold}-parent anchor consensus`,
    fixedPointReason: "No frozen candidate has enough independent parent witnesses for another non-conflicting oxygen anchor.",
    provenance: { ...artifact.provenance },
  };
}
