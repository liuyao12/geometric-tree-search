// Curated, checked entries from I. D. Brown's IUCr bvparm2020.cif table.
// Source: https://www.iucr.org/resources/data/data-sets/bond-valence-parameters
// Source dataset SHA-256: 6f921b6fd20b00fdbe4705a38f02e5c45ae91f1c39be55eb6b0620a454875b89
// The table is ordered by stated reliability. We retain only explicit, checked
// pairs exercised by the portal and fail closed for everything else.
export const BOND_VALENCE_PROVENANCE = Object.freeze({
  dataset: "IUCr bvparm2020.cif",
  revision: "2020-11-25",
  source: "https://www.iucr.org/resources/data/data-sets/bond-valence-parameters",
  sha256: "6f921b6fd20b00fdbe4705a38f02e5c45ae91f1c39be55eb6b0620a454875b89",
  equation: "s = exp((R0 - R) / B)",
  vectorEquation: "V_i = sum_j s_ij rhat_ij",
  vectorRuleDoi: "10.1107/S0108768106026553",
  vectorRuleScope: "near-zero resultant is expected for a stable spherically symmetric coordination sphere",
  vectorRuleCaveat: "lone pairs and electronic or steric anisotropy can produce a physically meaningful nonzero resultant",
  units: "angstrom and valence units",
});

const PARAMETERS = Object.freeze([
  // O-H is explicitly range-dependent in bvparm2020; one global pair is invalid.
  { cation: "H", cationCharge: 1, anion: "O", anionCharge: -2,
    r0: .907, b: .28, minimumDistance: 0, maximumDistance: 1.05,
    reference: "bc", note: "O-H < 1.05 A" },
  { cation: "H", cationCharge: 1, anion: "O", anionCharge: -2,
    r0: .569, b: .94, minimumDistance: 1.05, maximumDistance: 1.70,
    reference: "bc", note: "1.05 < O-H < 1.70 A; best general value" },
  { cation: "H", cationCharge: 1, anion: "O", anionCharge: -2,
    r0: .990, b: .59, minimumDistance: 1.70, maximumDistance: 3.0,
    reference: "bc", note: "1.70 A < O-H; portal cutoff 3.0 A" },
  { cation: "Na", cationCharge: 1, anion: "O", anionCharge: -2,
    r0: 1.803, b: .37, minimumDistance: 0, maximumDistance: 3.0,
    reference: "a", note: "first checked IUCr occurrence; portal cutoff 3.0 A" },
  { cation: "Na", cationCharge: 1, anion: "Cl", anionCharge: -1,
    r0: 2.15, b: .37, minimumDistance: 0, maximumDistance: 3.4,
    reference: "b", note: "first checked IUCr occurrence; portal cutoff 3.4 A" },
  { cation: "Cu", cationCharge: 2, anion: "O", anionCharge: -2,
    r0: 1.679, b: .36, minimumDistance: 0, maximumDistance: 3.0,
    reference: "bj", note: "first checked IUCr occurrence; portal cutoff 3.0 A" },
].map(Object.freeze));

export const BOND_VALENCE_PARAMETERS = PARAMETERS;
export const MAXIMUM_BOND_VALENCE_DISTANCE = Math.max(...PARAMETERS.map((record) => record.maximumDistance));

function finiteSite(site) {
  return typeof site?.species === "string" && site.species.length > 0
    && Array.isArray(site.position) && site.position.length === 3
    && site.position.every(Number.isFinite) && Number.isFinite(site.charge)
    && Math.abs(site.charge) > 1e-12;
}

function distance(first, second) {
  return Math.hypot(...first.position.map((value, axis) => value - second.position[axis]));
}

function orientedIons(first, second) {
  if (first.charge > 0 && second.charge < 0) return [first, second];
  if (second.charge > 0 && first.charge < 0) return [second, first];
  return null;
}

export function bondValenceParameter(first, second, separation) {
  const ions = orientedIons(first, second);
  if (!ions || !Number.isFinite(separation) || separation <= 0) return null;
  const [cation, anion] = ions;
  return PARAMETERS.find((record) => record.cation === cation.species
    && Math.abs(record.cationCharge - cation.charge) <= 1e-9
    && record.anion === anion.species
    && Math.abs(record.anionCharge - anion.charge) <= 1e-9
    && separation > record.minimumDistance - 1e-12
    && separation <= record.maximumDistance + 1e-12) || null;
}

function siteKey(site) {
  return `${site.species}${site.charge >= 0 ? "+" : ""}${site.charge}`;
}

export function bondValenceSums(sites = []) {
  const valid = sites.filter(finiteSite);
  const sums = new Array(valid.length).fill(0);
  const vectors = valid.map(() => [0, 0, 0]);
  const bondCounts = new Array(valid.length).fill(0);
  const usedParameters = new Map();
  const missingPairTypes = new Set();
  let pairCount = 0;
  let distanceEvaluations = 0;
  for (let first = 0; first < valid.length; first++) for (let second = first + 1; second < valid.length; second++) {
    const ions = orientedIons(valid[first], valid[second]);
    if (!ions) continue;
    const separation = distance(valid[first], valid[second]);
    distanceEvaluations++;
    const parameter = bondValenceParameter(valid[first], valid[second], separation);
    if (!parameter) {
      if (separation <= MAXIMUM_BOND_VALENCE_DISTANCE) {
        missingPairTypes.add(`${siteKey(ions[0])}–${siteKey(ions[1])}`);
      }
      continue;
    }
    const valence = Math.exp((parameter.r0 - separation) / parameter.b);
    sums[first] += valence; sums[second] += valence;
    for (let axis = 0; axis < 3; axis++) {
      const component = valence * (valid[second].position[axis] - valid[first].position[axis]) / separation;
      vectors[first][axis] += component;
      vectors[second][axis] -= component;
    }
    bondCounts[first]++; bondCounts[second]++; pairCount++;
    const parameterKey = `${parameter.cation}+${parameter.cationCharge}/${parameter.anion}${parameter.anionCharge}`;
    usedParameters.set(parameterKey, parameter);
  }
  const records = valid.map((site, index) => {
    const target = Math.abs(site.charge);
    const residual = sums[index] - target;
    const vectorMagnitude = Math.hypot(...vectors[index]);
    return { species: site.species, charge: site.charge, position: [...site.position],
      target, sum: sums[index], residual, absoluteResidual: Math.abs(residual),
      vectorSum: [...vectors[index]], vectorMagnitude,
      normalizedVectorImbalance: bondCounts[index] > 0
        ? vectorMagnitude / Math.max(sums[index], target, 1e-12) : null,
      bondCount: bondCounts[index], resolved: bondCounts[index] > 0,
      state: residual < -.1 ? "underbonded" : residual > .1 ? "overbonded" : "satisfied" };
  });
  const resolved = records.filter((record) => record.resolved);
  return {
    available: pairCount > 0,
    sites: records,
    pairCount,
    distanceEvaluations,
    resolvedSites: resolved.length,
    unresolvedSites: records.length - resolved.length,
    meanAbsoluteResidual: resolved.length
      ? resolved.reduce((sum, record) => sum + record.absoluteResidual, 0) / resolved.length : null,
    maximumAbsoluteResidual: resolved.length
      ? Math.max(...resolved.map((record) => record.absoluteResidual)) : null,
    meanVectorMagnitude: resolved.length
      ? resolved.reduce((sum, record) => sum + record.vectorMagnitude, 0) / resolved.length : null,
    maximumVectorMagnitude: resolved.length
      ? Math.max(...resolved.map((record) => record.vectorMagnitude)) : null,
    usedParameters: [...usedParameters.entries()].map(([key, value]) => ({ key, ...value })),
    missingPairTypes: [...missingPairTypes].sort(),
  };
}

export function incrementalBondValenceSatisfaction(currentSites = [], addedSites = []) {
  const current = currentSites.filter(finiteSite);
  const added = addedSites.filter(finiteSite);
  if (!current.length || !added.length) return {
    available: false, score: 0, reason: !current.length ? "current charged neighborhood unavailable"
      : "candidate adds no charged sites", currentSites: current.length, addedSites: added.length,
    targetUsed: false, candidateGeometryChanged: false, hardAdmissionChanged: false,
  };
  const before = bondValenceSums(current);
  const after = bondValenceSums([...current, ...added]);
  const addedOffset = current.length;
  const affectedCurrentIndices = new Set();
  for (let index = 0; index < current.length; index++) {
    if (added.some((site) => bondValenceParameter(current[index], site, distance(current[index], site)))) {
      affectedCurrentIndices.add(index);
    }
  }
  const addedRecords = after.sites.slice(addedOffset);
  const resolvedAdded = addedRecords.filter((record) => record.resolved);
  if (!resolvedAdded.length) return {
    available: false, score: 0, reason: "no checked bond-valence parameter connects the candidate",
    currentSites: current.length, addedSites: added.length,
    missingPairTypes: after.missingPairTypes,
    distanceEvaluations: before.distanceEvaluations + after.distanceEvaluations,
    targetUsed: false, candidateGeometryChanged: false, hardAdmissionChanged: false,
  };
  const beforeBurden = [...affectedCurrentIndices].reduce((sum, index) =>
    sum + before.sites[index].absoluteResidual, 0)
    + added.reduce((sum, site) => sum + Math.abs(site.charge), 0);
  const afterBurden = [...affectedCurrentIndices].reduce((sum, index) =>
    sum + after.sites[index].absoluteResidual, 0)
    + addedRecords.reduce((sum, record) => sum + record.absoluteResidual, 0);
  const denominator = Math.max(beforeBurden + afterBurden, 1e-12);
  const score = (beforeBurden - afterBurden) / denominator;
  const beforeVectorBurden = [...affectedCurrentIndices].reduce((sum, index) =>
    sum + (before.sites[index].resolved ? before.sites[index].vectorMagnitude : before.sites[index].target), 0)
    + added.reduce((sum, site) => sum + Math.abs(site.charge), 0);
  const afterVectorBurden = [...affectedCurrentIndices].reduce((sum, index) =>
    sum + after.sites[index].vectorMagnitude, 0)
    + addedRecords.reduce((sum, record) => sum + record.vectorMagnitude, 0);
  const vectorDenominator = Math.max(beforeVectorBurden + afterVectorBurden, 1e-12);
  const vectorScore = (beforeVectorBurden - afterVectorBurden) / vectorDenominator;
  const combinedScore = .5 * (score + vectorScore);
  const affectedSites = [
    ...[...affectedCurrentIndices].map((index) => ({ role: "existing", before: before.sites[index], after: after.sites[index] })),
    ...addedRecords.map((record) => ({ role: "added", before: {
      ...record, sum: 0, residual: -record.target, absoluteResidual: record.target,
      vectorSum: null, vectorMagnitude: record.target, normalizedVectorImbalance: 1,
      bondCount: 0, resolved: false, state: "underbonded" }, after: record })),
  ];
  return {
    available: true, score, scalarScore: score, vectorScore, combinedScore,
    beforeBurden, afterBurden, beforeVectorBurden, afterVectorBurden,
    burdenReduction: beforeBurden - afterBurden,
    vectorBurdenReduction: beforeVectorBurden - afterVectorBurden,
    affectedSites, affectedExistingSites: affectedCurrentIndices.size,
    addedSites: added.length, resolvedAddedSites: resolvedAdded.length,
    pairCountBefore: before.pairCount, pairCountAfter: after.pairCount,
    addedBondCount: after.pairCount - before.pairCount,
    usedParameters: after.usedParameters,
    missingPairTypes: after.missingPairTypes,
    distanceEvaluations: before.distanceEvaluations + after.distanceEvaluations,
    provenance: BOND_VALENCE_PROVENANCE,
    suppliedOxidationStatesOnly: true,
    oxidationStatesInferred: false,
    translationInvariant: true,
    properRotationInvariant: true,
    uniformScaleInvariant: false,
    physicalAngstromScaleRequired: true,
    vectorRuleScope: BOND_VALENCE_PROVENANCE.vectorRuleScope,
    anisotropyCanBePhysical: true,
    lonePairModeled: false,
    electronicAnisotropyModeled: false,
    stericAnisotropyModeled: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    bondEnergyInferred: false,
    electrostaticEnergyInferred: false,
    electronDensityModeled: false,
    chargeTransferModeled: false,
    forcesIntegrated: false,
    physicalTimeIntegrated: false,
  };
}
