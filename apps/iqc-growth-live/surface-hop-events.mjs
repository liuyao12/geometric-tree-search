const finite = (value) => Number.isFinite(Number(value));

function normalizedSite(site, label) {
  if (typeof site?.species !== "string" || !site.species.trim()
      || !Array.isArray(site.positionAngstrom) || site.positionAngstrom.length !== 3
      || !site.positionAngstrom.every(finite)) {
    throw new TypeError(`${label} must contain species and a finite Cartesian position`);
  }
  return { species: site.species.trim(), positionAngstrom: site.positionAngstrom.map(Number) };
}

function siteKey(site) {
  return `${site.species}\u0000${site.positionAngstrom.map((value) =>
    value.toPrecision(15)).join(",")}`;
}

function speciesSignature(sites) {
  const counts = new Map();
  sites.forEach((site) => counts.set(site.species, (counts.get(site.species) || 0) + 1));
  return [...counts].sort(([first], [second]) => first.localeCompare(second))
    .map(([species, count]) => `${species}:${count}`).join("|");
}

function centroid(sites) {
  return [0, 1, 2].map((axis) => sites.reduce((sum, site) =>
    sum + site.positionAngstrom[axis], 0) / sites.length);
}

function distance(first, second) {
  return Math.hypot(...first.map((value, axis) => value - second[axis]));
}

function uniqueSites(sites) {
  return [...new Map(sites.map((site) => [siteKey(site), site])).values()]
    .sort((first, second) => siteKey(first).localeCompare(siteKey(second)));
}

export function enumerateMassConservingSurfaceHops({ sources, destinations,
  maximumCentroidDistanceAngstrom, maximumEvents = 512 } = {}) {
  if (!Array.isArray(sources) || !Array.isArray(destinations)) {
    throw new TypeError("surface-hop enumeration needs source and destination arrays");
  }
  if (!finite(maximumCentroidDistanceAngstrom) || Number(maximumCentroidDistanceAngstrom) <= 0) {
    throw new RangeError("surface-hop reach must be a positive finite distance in angstroms");
  }
  if (!Number.isInteger(maximumEvents) || maximumEvents < 1) {
    throw new RangeError("maximumEvents must be a positive integer");
  }
  const normalizedSources = sources.map((source, index) => ({
    sourcePlacementId: Number(source.sourcePlacementId),
    clusterType: String(source.clusterType),
    ruleId: String(source.ruleId),
    removableAtomIds: (source.removableAtomIds || []).filter(Number.isInteger).sort((a, b) => a - b),
    removedSites: (source.removedSites || []).map((site, siteIndex) =>
      normalizedSite(site, `source ${index + 1} removed site ${siteIndex + 1}`)),
    actionSites: (source.actionSites || []).map((site, siteIndex) =>
      normalizedSite(site, `source ${index + 1} action site ${siteIndex + 1}`)),
    admitted: source.admitted === true,
    targetUsed: source.targetUsed === true,
  }));
  const normalizedDestinations = destinations.map((destination, index) => ({
    destinationCandidateId: String(destination.destinationCandidateId || ""),
    parentPlacementId: Number(destination.parentPlacementId),
    clusterType: String(destination.clusterType),
    ruleId: String(destination.ruleId),
    mergedAtomIds: (destination.mergedAtomIds || []).filter(Number.isInteger).sort((a, b) => a - b),
    emittedSites: (destination.emittedSites || []).map((site, siteIndex) =>
      normalizedSite(site, `destination ${index + 1} emitted site ${siteIndex + 1}`)),
    actionSites: (destination.actionSites || []).map((site, siteIndex) =>
      normalizedSite(site, `destination ${index + 1} action site ${siteIndex + 1}`)),
    admitted: destination.admitted === true,
    targetUsed: destination.targetUsed === true,
  }));
  const admitted = [];
  const rejected = [];
  normalizedSources.forEach((source) => normalizedDestinations.forEach((destination) => {
    const reasons = [];
    if (!Number.isInteger(source.sourcePlacementId) || !source.admitted || source.targetUsed) {
      reasons.push("source-not-ownership-certified");
    }
    if (!destination.destinationCandidateId || !Number.isInteger(destination.parentPlacementId)
        || !destination.admitted || destination.targetUsed) {
      reasons.push("destination-not-hard-admitted");
    }
    if (source.sourcePlacementId === destination.parentPlacementId) {
      reasons.push("destination-depends-on-source-leaf");
    }
    if (source.clusterType !== destination.clusterType) reasons.push("cluster-type-changed");
    if (!source.removedSites.length || !destination.emittedSites.length) {
      reasons.push("empty-transfer-support");
    }
    if (speciesSignature(source.removedSites) !== speciesSignature(destination.emittedSites)) {
      reasons.push("species-population-not-conserved");
    }
    const removable = new Set(source.removableAtomIds);
    if (destination.mergedAtomIds.some((atomId) => removable.has(atomId))) {
      reasons.push("destination-uses-removed-source-atom");
    }
    const removedKeys = new Set(source.removedSites.map(siteKey));
    if (destination.emittedSites.some((site) => removedKeys.has(siteKey(site)))) {
      reasons.push("stationary-delete-recreate-site");
    }
    const hopDistanceAngstrom = source.removedSites.length && destination.emittedSites.length
      ? distance(centroid(source.removedSites), centroid(destination.emittedSites)) : Infinity;
    if (hopDistanceAngstrom > Number(maximumCentroidDistanceAngstrom)) {
      reasons.push("outside-local-hop-reach");
    }
    const record = {
      candidateId: `hop:${source.sourcePlacementId}->${destination.destinationCandidateId}`,
      eventDirection: "hop",
      sourcePlacementId: source.sourcePlacementId,
      destinationCandidateId: destination.destinationCandidateId,
      parentPlacementId: destination.parentPlacementId,
      clusterType: destination.clusterType,
      sourceRuleId: source.ruleId,
      destinationRuleId: destination.ruleId,
      removableAtomIds: source.removableAtomIds,
      removedSites: source.removedSites,
      emittedSites: destination.emittedSites,
      actionSites: uniqueSites([...source.actionSites, ...destination.actionSites]),
      hopDistanceAngstrom,
      atomCountChange: 0,
      speciesPopulationConserved: !reasons.includes("species-population-not-conserved"),
      sourceIndependentDestination: !reasons.includes("destination-depends-on-source-leaf")
        && !reasons.includes("destination-uses-removed-source-atom"),
      admitted: reasons.length === 0,
      reasons,
      targetUsed: false,
    };
    (record.admitted ? admitted : rejected).push(record);
  }));
  admitted.sort((first, second) => first.hopDistanceAngstrom - second.hopDistanceAngstrom
    || first.candidateId.localeCompare(second.candidateId));
  const retained = admitted.slice(0, maximumEvents);
  return {
    schema: "gcts-mass-conserving-surface-hop-catalog-v1",
    sourceCount: normalizedSources.length,
    destinationCount: normalizedDestinations.length,
    consideredPairCount: normalizedSources.length * normalizedDestinations.length,
    admittedBeforeCap: admitted.length,
    admitted: retained,
    rejected,
    omittedByFiniteCap: admitted.length - retained.length,
    maximumEvents,
    maximumCentroidDistanceAngstrom: Number(maximumCentroidDistanceAngstrom),
    atomCountConserved: true,
    speciesPopulationConserved: true,
    exactInitialAndFinalGeometryRequired: true,
    barrierAndPrefactorInferred: false,
    intermediateTrajectoryInferred: false,
    targetUsed: false,
    catalogCompleteBeyondFrozenPairs: false,
    claimBoundary: "Each event moves one ownership-certified leaf support to one independent hard-admitted destination of the same colored population. The exact endpoints are frozen, but the migration path, saddle, barrier, prefactor, recrossing, and omitted hop mechanisms require external evidence.",
  };
}
