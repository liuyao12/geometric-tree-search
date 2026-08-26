function finiteSite(site) {
  return Array.isArray(site?.position) && site.position.length === 3
    && site.position.every(Number.isFinite) && Number.isFinite(site.charge);
}

function distance(first, second) {
  return Math.hypot(...first.position.map((value, axis) => value - second.position[axis]));
}

export function incrementalIonicPairGeometry(currentSites = [], addedSites = [], options = {}) {
  const current = currentSites.filter(finiteSite);
  const added = addedSites.filter(finiteSite);
  const nearestNeighborScale = Number(options.nearestNeighborScale);
  const reachNearestNeighborUnits = options.reachNearestNeighborUnits === "global"
    ? Infinity : Number(options.reachNearestNeighborUnits);
  const available = current.length > 0 && added.length > 0 && nearestNeighborScale > 0
    && (reachNearestNeighborUnits > 0 || reachNearestNeighborUnits === Infinity);
  if (!available) return { available: false, score: 0, pairCount: 0,
    currentSites: current.length, addedSites: added.length,
    reason: !current.length ? "current charged solid unavailable" : !added.length ? "candidate adds no charged sites"
      : !(nearestNeighborScale > 0) ? "nearest-neighbor scale unavailable" : "invalid ionic-pair reach" };
  let signedPairSum = 0;
  let absolutePairSum = 0;
  let attractiveMagnitude = 0;
  let repulsiveMagnitude = 0;
  let pairCount = 0;
  let distanceEvaluations = 0;
  const accumulate = (first, second) => {
    const normalizedDistance = distance(first, second) / nearestNeighborScale;
    distanceEvaluations++;
    if (!(normalizedDistance > 1e-12) || normalizedDistance > reachNearestNeighborUnits) return;
    const term = first.charge * second.charge / normalizedDistance;
    signedPairSum += term;
    absolutePairSum += Math.abs(term);
    if (term < 0) attractiveMagnitude += -term;
    else repulsiveMagnitude += term;
    pairCount++;
  };
  added.forEach((site) => current.forEach((neighbor) => accumulate(site, neighbor)));
  added.forEach((site, index) => added.slice(index + 1).forEach((neighbor) => accumulate(site, neighbor)));
  const normalizedSignedPairSum = absolutePairSum > 1e-15 ? signedPairSum / absolutePairSum : 0;
  return { available: pairCount > 0, score: -normalizedSignedPairSum,
    signedPairSum, absolutePairSum, normalizedSignedPairSum,
    attractiveMagnitude, repulsiveMagnitude, pairCount, distanceEvaluations,
    currentSites: current.length, addedSites: added.length,
    nearestNeighborScale, reachNearestNeighborUnits: Number.isFinite(reachNearestNeighborUnits)
      ? reachNearestNeighborUnits : "global",
    incrementalPairsOnly: true, currentCurrentConstantOmitted: true,
    translationInvariant: true, properRotationInvariant: true, uniformScaleInvariant: true,
    candidateGeometryChanged: false, hardAdmissionChanged: false, targetUsed: false,
    suppliedFormalChargeOnly: true, coulombKernelUsed: true,
    coulombPrefactorApplied: false, dielectricConstantApplied: false,
    periodicImagesUsed: false, ewaldSummationUsed: false, neutralizingBackgroundUsed: false,
    electrostaticEnergyInferred: false, electrostaticPotentialSolved: false,
    polarizationModeled: false, chargeTransferModeled: false,
    electronicStructureModeled: false, physicalTimeIntegrated: false };
}

export function incrementalIonicPairReachProfile(currentSites = [], addedSites = [], options = {}) {
  const reaches = [...new Set((options.reaches || [2, 4, 8, "global"])
    .map((reach) => reach === "global" ? "global" : Number(reach)))]
    .filter((reach) => reach === "global" || Number.isFinite(reach) && reach > 0);
  const samples = reaches.map((reach) => incrementalIonicPairGeometry(currentSites, addedSites, {
    nearestNeighborScale: options.nearestNeighborScale,
    reachNearestNeighborUnits: reach,
  }));
  const available = samples.some((sample) => sample.available);
  const scores = samples.filter((sample) => sample.available).map((sample) => sample.score);
  const signedSums = samples.filter((sample) => sample.available).map((sample) => sample.signedPairSum);
  return {
    available,
    samples: samples.map((sample, index) => ({ ...sample, reach: reaches[index] })),
    scoreSpread: scores.length ? Math.max(...scores) - Math.min(...scores) : 0,
    signedPairSumSpread: signedSums.length ? Math.max(...signedSums) - Math.min(...signedSums) : 0,
    distanceEvaluations: samples.reduce((sum, sample) => sum + (sample.distanceEvaluations || 0), 0),
    reaches,
    fixedBeforeCandidateRanking: true,
    candidateSetChanged: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    dielectricOrEwaldConvergenceInferred: false,
    thermodynamicLimitInferred: false,
  };
}

export function rankIonicPairReachProfiles(records = []) {
  const usable = records.filter((record) => record?.candidateKey && record.profile?.samples?.length);
  if (!usable.length) return { available: false, reaches: [], candidates: [], winners: [],
    uniqueWinners: 0, adjacentWinnerChanges: 0, rankReversalCandidates: 0 };
  const reaches = [...usable[0].profile.reaches];
  const rankings = reaches.map((reach, index) => usable
    .filter((record) => record.profile.samples[index]?.available)
    .sort((first, second) => second.profile.samples[index].score - first.profile.samples[index].score
      || first.candidateKey.localeCompare(second.candidateKey)));
  const rankMaps = rankings.map((ranking) => new Map(ranking.map((record, index) => [record.candidateKey, index + 1])));
  const candidates = usable.map((record) => ({ candidateKey: record.candidateKey,
    ranks: rankMaps.map((rankMap) => rankMap.get(record.candidateKey) ?? null),
  })).sort((first, second) => first.candidateKey.localeCompare(second.candidateKey));
  const winners = rankings.map((ranking, index) => ({ reach: reaches[index],
    candidateKey: ranking[0]?.candidateKey ?? null,
    score: ranking[0]?.profile.samples[index].score ?? null }));
  return {
    available: true, reaches, candidates, winners,
    uniqueWinners: new Set(winners.map((winner) => winner.candidateKey).filter(Boolean)).size,
    adjacentWinnerChanges: winners.slice(1).filter((winner, index) =>
      winner.candidateKey !== winners[index].candidateKey).length,
    rankReversalCandidates: candidates.filter((candidate) =>
      new Set(candidate.ranks.filter(Number.isFinite)).size > 1).length,
    stableTieBreak: "candidate key lexical order",
    candidateSetChanged: false, candidateGeometryChanged: false,
    hardAdmissionChanged: false, targetUsed: false,
  };
}
