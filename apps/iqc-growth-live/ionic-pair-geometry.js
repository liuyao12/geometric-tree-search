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
