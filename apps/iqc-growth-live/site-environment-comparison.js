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
  const species = [...new Set([...firstCounts.keys(), ...secondCounts.keys(),
    ...firstShells.keys(), ...secondShells.keys()])].sort();
  const coordination = species.map((symbol) => ({ species: symbol,
    first: firstCounts.get(symbol) || 0, second: secondCounts.get(symbol) || 0,
    delta: (secondCounts.get(symbol) || 0) - (firstCounts.get(symbol) || 0) }));
  let squared = 0; let matchedDistances = 0; let unmatchedDistances = 0;
  const radialShells = species.map((symbol) => {
    const left = firstShells.get(symbol) || [];
    const right = secondShells.get(symbol) || [];
    const matched = Math.min(left.length, right.length);
    let localSquared = 0;
    for (let index = 0; index < matched; index++) localSquared += (right[index] - left[index]) ** 2;
    squared += localSquared; matchedDistances += matched;
    unmatchedDistances += Math.abs(left.length - right.length);
    return { species: symbol, matched, unmatched: Math.abs(left.length - right.length),
      rmsDistanceDeltaAngstrom: matched ? rounded(Math.sqrt(localSquared / matched)) : null };
  });
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
    radialShells: { channels: radialShells, matchedDistances, unmatchedDistances,
      rmsDistanceDeltaAngstrom: matchedDistances ? rounded(Math.sqrt(squared / matchedDistances)) : null },
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
      energyEquivalenceInferred: false, physicalMechanismInferred: false },
  };
  comparison.comparisonDigest = stableDigest(comparison);
  return comparison;
}
