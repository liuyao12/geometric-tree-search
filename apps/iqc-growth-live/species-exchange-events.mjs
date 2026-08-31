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

function speciesCounts(sites) {
  const result = new Map();
  sites.forEach((site) => result.set(site.species, (result.get(site.species) || 0) + 1));
  return result;
}

function speciesDelta(removedSites, emittedSites) {
  const removed = speciesCounts(removedSites); const emitted = speciesCounts(emittedSites);
  return Object.fromEntries([...new Set([...removed.keys(), ...emitted.keys()])].sort()
    .map((species) => [species, (emitted.get(species) || 0) - (removed.get(species) || 0)])
    .filter(([, delta]) => delta !== 0));
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

export function enumerateLocalSpeciesExchangeEvents({ sources, destinations,
  maximumCentroidDistanceAngstrom, maximumEvents = 512 } = {}) {
  if (!Array.isArray(sources) || !Array.isArray(destinations)) {
    throw new TypeError("species-exchange enumeration needs source and destination arrays");
  }
  if (!finite(maximumCentroidDistanceAngstrom) || Number(maximumCentroidDistanceAngstrom) <= 0) {
    throw new RangeError("species-exchange reach must be a positive finite distance in angstroms");
  }
  if (!Number.isInteger(maximumEvents) || maximumEvents < 1) {
    throw new RangeError("maximumEvents must be a positive integer");
  }
  const normalizedSources = sources.map((source, index) => ({
    sourcePlacementId: Number(source.sourcePlacementId),
    clusterType: String(source.clusterType), ruleId: String(source.ruleId),
    removableAtomIds: (source.removableAtomIds || []).filter(Number.isInteger).sort((a, b) => a - b),
    removedSites: (source.removedSites || []).map((site, siteIndex) =>
      normalizedSite(site, `source ${index + 1} removed site ${siteIndex + 1}`)),
    actionSites: (source.actionSites || []).map((site, siteIndex) =>
      normalizedSite(site, `source ${index + 1} action site ${siteIndex + 1}`)),
    admitted: source.admitted === true, targetUsed: source.targetUsed === true,
  }));
  const normalizedDestinations = destinations.map((destination, index) => ({
    destinationCandidateId: String(destination.destinationCandidateId || ""),
    parentPlacementId: Number(destination.parentPlacementId),
    clusterType: String(destination.clusterType), ruleId: String(destination.ruleId),
    mergedAtomIds: (destination.mergedAtomIds || []).filter(Number.isInteger).sort((a, b) => a - b),
    emittedSites: (destination.emittedSites || []).map((site, siteIndex) =>
      normalizedSite(site, `destination ${index + 1} emitted site ${siteIndex + 1}`)),
    actionSites: (destination.actionSites || []).map((site, siteIndex) =>
      normalizedSite(site, `destination ${index + 1} action site ${siteIndex + 1}`)),
    admitted: destination.admitted === true, targetUsed: destination.targetUsed === true,
  }));
  const admitted = []; const rejected = [];
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
    if (!source.removedSites.length || !destination.emittedSites.length) {
      reasons.push("empty-transfer-support");
    }
    if (source.removedSites.length !== destination.emittedSites.length) {
      reasons.push("atom-count-not-conserved");
    }
    const delta = speciesDelta(source.removedSites, destination.emittedSites);
    if (!Object.keys(delta).length) reasons.push("no-species-exchange");
    if (Object.values(delta).reduce((sum, value) => sum + value, 0) !== 0) {
      reasons.push("species-delta-does-not-conserve-atom-count");
    }
    const removable = new Set(source.removableAtomIds);
    if (destination.mergedAtomIds.some((atomId) => removable.has(atomId))) {
      reasons.push("destination-uses-removed-source-atom");
    }
    const exchangeDistanceAngstrom = source.removedSites.length && destination.emittedSites.length
      ? distance(centroid(source.removedSites), centroid(destination.emittedSites)) : Infinity;
    if (exchangeDistanceAngstrom > Number(maximumCentroidDistanceAngstrom)) {
      reasons.push("outside-local-exchange-reach");
    }
    const record = {
      candidateId: `exchange:${source.sourcePlacementId}->${destination.destinationCandidateId}`,
      eventDirection: "exchange", sourcePlacementId: source.sourcePlacementId,
      destinationCandidateId: destination.destinationCandidateId,
      parentPlacementId: destination.parentPlacementId,
      sourceClusterType: source.clusterType, destinationClusterType: destination.clusterType,
      sourceRuleId: source.ruleId, destinationRuleId: destination.ruleId,
      removableAtomIds: source.removableAtomIds, removedSites: source.removedSites,
      emittedSites: destination.emittedSites,
      actionSites: uniqueSites([...source.actionSites, ...destination.actionSites]),
      exchangeDistanceAngstrom, atomCountChange: 0, speciesDelta: delta,
      speciesPopulationChanged: Object.keys(delta).length > 0,
      sourceIndependentDestination: !reasons.includes("destination-depends-on-source-leaf")
        && !reasons.includes("destination-uses-removed-source-atom"),
      admitted: reasons.length === 0, reasons, targetUsed: false,
    };
    (record.admitted ? admitted : rejected).push(record);
  }));
  admitted.sort((first, second) => first.exchangeDistanceAngstrom - second.exchangeDistanceAngstrom
    || first.candidateId.localeCompare(second.candidateId));
  const retained = admitted.slice(0, maximumEvents);
  return {
    schema: "gcts-local-species-exchange-catalog-v1",
    sourceCount: normalizedSources.length, destinationCount: normalizedDestinations.length,
    consideredPairCount: normalizedSources.length * normalizedDestinations.length,
    admittedBeforeCap: admitted.length, admitted: retained, rejected,
    omittedByFiniteCap: admitted.length - retained.length, maximumEvents,
    maximumCentroidDistanceAngstrom: Number(maximumCentroidDistanceAngstrom),
    atomCountConserved: true, speciesPopulationMustChange: true,
    exactReservoirSpeciesDeltaRequired: true, exactInitialAndFinalGeometryRequired: true,
    barrierPrefactorAndChemicalPotentialInferred: false, intermediateTrajectoryInferred: false,
    targetUsed: false, catalogCompleteBeyondFrozenPairs: false,
    claimBoundary: "Each event removes one ownership-certified leaf support and inserts one independent hard-admitted equal-count support with a different colored population. Exact endpoints and species deltas are frozen; reservoir chemical work, path, saddle, barrier, prefactor, recrossing, and omitted exchange mechanisms require external evidence.",
  };
}
