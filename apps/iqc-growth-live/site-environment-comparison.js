function finite(value, fallback = 0) {
  return Number.isFinite(Number(value)) ? Number(value) : fallback;
}

function rounded(value, digits = 5) {
  const scale = 10 ** digits;
  return Math.round(finite(value) * scale) / scale;
}

function entriesMap(entries) {
  return new Map(Array.isArray(entries) ? entries.map(([key, value]) => [String(key), finite(value)]) : []);
}

function shellsMap(entries) {
  return new Map(Array.isArray(entries) ? entries.map(([key, values]) => [String(key),
    (Array.isArray(values) ? values : []).map(Number).filter(Number.isFinite).sort((a, b) => a - b)]) : []);
}

function minimumMonotoneSquaredDifference(first, second, scale) {
  let shorter = first; let longer = second;
  if (shorter.length > longer.length) [shorter, longer] = [longer, shorter];
  if (!shorter.length) return 0;
  const table = Array.from({ length: shorter.length + 1 }, () => new Array(longer.length + 1).fill(Infinity));
  table[0].fill(0);
  for (let count = 1; count <= shorter.length; count++) {
    for (let available = count; available <= longer.length; available++) {
      const delta = (shorter[count - 1] - longer[available - 1]) * scale;
      table[count][available] = Math.min(table[count][available - 1],
        table[count - 1][available - 1] + delta * delta);
    }
  }
  return table[shorter.length][longer.length];
}

function compareShellMaps(firstShells, secondShells, scale = 1) {
  const channels = [...new Set([...firstShells.keys(), ...secondShells.keys()])].sort();
  let squared = 0; let matched = 0; let unmatched = 0;
  const records = channels.map((channel) => {
    const left = firstShells.get(channel) || []; const right = secondShells.get(channel) || [];
    const localMatched = Math.min(left.length, right.length);
    const localSquared = minimumMonotoneSquaredDifference(left, right, scale);
    squared += localSquared; matched += localMatched; unmatched += Math.abs(left.length - right.length);
    return { channel, matched: localMatched, unmatched: Math.abs(left.length - right.length),
      rmsDelta: localMatched ? rounded(Math.sqrt(localSquared / localMatched)) : null };
  });
  return { channels: records, matched, unmatched,
    rmsDelta: matched ? rounded(Math.sqrt(squared / matched)) : null };
}

function stableDigest(value) {
  const text = JSON.stringify(value);
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index++) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

/** Compare two finite colored local environments without using their absolute frames. */
export function compareSiteEnvironments({ first, second, firstConstraint = null, secondConstraint = null }) {
  if (!first?.localEnvironment || !second?.localEnvironment) {
    throw new Error("Two site-provenance snapshots are required");
  }
  const firstCounts = entriesMap(first.localEnvironment.speciesCounts);
  const secondCounts = entriesMap(second.localEnvironment.speciesCounts);
  const firstShells = shellsMap(first.localEnvironment.distanceShells);
  const secondShells = shellsMap(second.localEnvironment.distanceShells);
  const firstAngles = shellsMap(first.localEnvironment.angleShells);
  const secondAngles = shellsMap(second.localEnvironment.angleShells);
  const species = [...new Set([...firstCounts.keys(), ...secondCounts.keys(),
    ...firstShells.keys(), ...secondShells.keys()])].sort();
  const coordination = species.map((symbol) => ({ species: symbol,
    first: firstCounts.get(symbol) || 0, second: secondCounts.get(symbol) || 0,
    delta: (secondCounts.get(symbol) || 0) - (firstCounts.get(symbol) || 0) }));
  const radial = compareShellMaps(firstShells, secondShells);
  const angular = compareShellMaps(firstAngles, secondAngles);
  const orderFirst = entriesMap(first.localEnvironment.orientationalOrder);
  const orderSecond = entriesMap(second.localEnvironment.orientationalOrder);
  const orientationalOrder = [4, 6, 12].map((harmonic) => ({ harmonic,
    first: orderFirst.has(String(harmonic)) ? rounded(orderFirst.get(String(harmonic))) : null,
    second: orderSecond.has(String(harmonic)) ? rounded(orderSecond.get(String(harmonic))) : null,
    delta: orderFirst.has(String(harmonic)) && orderSecond.has(String(harmonic))
      ? rounded(orderSecond.get(String(harmonic)) - orderFirst.get(String(harmonic))) : null }));
  const firstSummary = firstConstraint?.summary || {};
  const secondSummary = secondConstraint?.summary || {};
  const delta = (key) => rounded(finite(secondSummary[key]) - finite(firstSummary[key]));
  const comparison = {
    schema: 1,
    centerChemistry: { first: String(first.species), second: String(second.species),
      sameSpecies: String(first.species) === String(second.species) },
    coordination: { channels: coordination,
      l1Difference: coordination.reduce((sum, channel) => sum + Math.abs(channel.delta), 0),
      firstTotal: finite(first.localEnvironment.coordination),
      secondTotal: finite(second.localEnvironment.coordination) },
    radialShells: { channels: radial.channels.map((record) => ({ species: record.channel,
      matched: record.matched, unmatched: record.unmatched,
      rmsDistanceDeltaAngstrom: record.rmsDelta })), matchedDistances: radial.matched,
      unmatchedDistances: radial.unmatched, rmsDistanceDeltaAngstrom: radial.rmsDelta },
    angularShells: { channels: angular.channels.map((record) => ({ speciesPair: record.channel,
      matched: record.matched, unmatched: record.unmatched, rmsAngleDeltaDegrees: record.rmsDelta })),
      matchedAngles: angular.matched, unmatchedAngles: angular.unmatched,
      rmsAngleDeltaDegrees: angular.rmsDelta },
    orientationalOrder: { dimension: first.localEnvironment.orientationalDimension === second.localEnvironment.orientationalDimension
      ? first.localEnvironment.orientationalDimension : null,
      definition: first.localEnvironment.orientationalDefinition === second.localEnvironment.orientationalDefinition
        ? first.localEnvironment.orientationalDefinition : "dimension mismatch",
      channels: orientationalOrder },
    constraintDelta: { available: Boolean(firstConstraint && secondConstraint),
      contactAngleMismatch: delta("contactAngleMismatch"), distanceMismatch: delta("distanceMismatch"),
      angleMismatch: delta("angleMismatch"), coordinationDeficit: delta("coordinationDeficit"),
      hardConflicts: delta("hardConflicts") },
    lineage: { firstOrigin: first.origin, secondOrigin: second.origin,
      firstDepth: finite(first.lineage?.causalDepth), secondDepth: finite(second.lineage?.causalDepth),
      depthDelta: finite(second.lineage?.causalDepth) - finite(first.lineage?.causalDepth),
      firstInterface: first.lineage?.interfaceSite === true, secondInterface: second.lineage?.interfaceSite === true },
    audit: { targetUsed: false, absoluteCoordinatesUsed: false, translationIndependent: true,
      globalRotationIndependent: true, fullLocalIsometryProved: false, defectIdentityInferred: false,
      angularPermutationResolved: false,
      energyEquivalenceInferred: false, physicalMechanismInferred: false },
  };
  comparison.comparisonDigest = stableDigest(comparison);
  return comparison;
}
