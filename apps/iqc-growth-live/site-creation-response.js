import { bestAffineNeighborhoodResidual } from "./relaxation-local-environment.js?v=20260826-2";

function finiteVector(value) {
  return Array.isArray(value) && value.length === 3 && value.every(Number.isFinite);
}

function magnitude(vector) {
  return Math.hypot(...vector);
}

function rounded(value, digits = 5) {
  if (!Number.isFinite(value)) return null;
  const scale = 10 ** digits;
  return Math.round(value * scale) / scale;
}

/** Compare an emitted site's frozen pre-projection shell with its current shell. */
export function buildSiteCreationResponse(creation, current) {
  if (!creation) return {
    available: false, status: "supplied site · no creation geometry",
    targetUsed: false, physicalDynamicsIntegrated: false,
  };
  if (!finiteVector(creation.centerPositionAngstrom) || !(creation.reachAngstrom > 0)
      || !Array.isArray(creation.neighbors) || !finiteVector(current?.centerPositionAngstrom)
      || !Array.isArray(current?.neighbors)) {
    throw new Error("creation response needs finite creation/current centers and neighbor shells");
  }
  const validateNeighbor = (neighbor) => neighbor && neighbor.siteId !== undefined
    && typeof neighbor.species === "string" && finiteVector(neighbor.vectorAngstrom);
  if (!creation.neighbors.every(validateNeighbor) || !current.neighbors.every(validateNeighbor)) {
    throw new Error("creation response neighbor records must retain site identity, species, and finite vectors");
  }
  const createdById = new Map(creation.neighbors.map((neighbor) => [String(neighbor.siteId), neighbor]));
  const currentById = new Map(current.neighbors.map((neighbor) => [String(neighbor.siteId), neighbor]));
  const persistent = creation.neighbors.filter((neighbor) => {
    const observed = currentById.get(String(neighbor.siteId));
    return observed && observed.species === neighbor.species;
  });
  const lost = creation.neighbors.filter((neighbor) => !persistent.includes(neighbor));
  const gained = current.neighbors.filter((neighbor) => !createdById.has(String(neighbor.siteId)));
  const sourceVectors = persistent.map((neighbor) => neighbor.vectorAngstrom);
  const targetVectors = persistent.map((neighbor) => currentById.get(String(neighbor.siteId)).vectorAngstrom);
  const radialDeltas = sourceVectors.map((source, index) => magnitude(targetVectors[index]) - magnitude(source));
  const vectorDeltas = sourceVectors.map((source, index) => Math.hypot(...source.map(
    (value, axis) => targetVectors[index][axis] - value)));
  let affine = null;
  if (persistent.length >= 3) {
    affine = bestAffineNeighborhoodResidual(sourceVectors, targetVectors);
  }
  const centerDisplacementAngstrom = Math.hypot(...creation.centerPositionAngstrom.map(
    (value, axis) => current.centerPositionAngstrom[axis] - value));
  const radialRmsAngstrom = radialDeltas.length
    ? Math.sqrt(radialDeltas.reduce((sum, value) => sum + value * value, 0) / radialDeltas.length) : null;
  const neighborVectorRmsAngstrom = vectorDeltas.length
    ? Math.sqrt(vectorDeltas.reduce((sum, value) => sum + value * value, 0) / vectorDeltas.length) : null;
  return {
    available: true,
    status: `${persistent.length}/${creation.neighbors.length} creation neighbors retained · ${gained.length} gained`,
    reachAngstrom: rounded(creation.reachAngstrom),
    creationNeighborCount: creation.neighbors.length,
    currentNeighborCount: current.neighbors.length,
    persistentNeighborCount: persistent.length,
    lostNeighborCount: lost.length,
    gainedNeighborCount: gained.length,
    lostNeighbors: lost.map(({ siteId, species }) => ({ siteId, species })),
    gainedNeighbors: gained.map(({ siteId, species }) => ({ siteId, species })),
    centerDisplacementAngstrom: rounded(centerDisplacementAngstrom),
    radialRmsAngstrom: rounded(radialRmsAngstrom),
    neighborVectorRmsAngstrom: rounded(neighborVectorRmsAngstrom),
    rootD2MinAngstrom: rounded(affine?.rootD2Min),
    normalizedRootD2Min: rounded(affine?.normalizedRootD2Min),
    affineResolved: affine?.fullRankSource === true,
    equivalentShearStrain: rounded(affine?.equivalentShearStrain),
    localVolumeChangeFraction: rounded(affine?.localVolumeChangeFraction),
    orientationPreserving: affine?.orientationPreserving ?? null,
    exactNeighborIdentityPairing: true,
    targetUsed: false,
    physicalDynamicsIntegrated: false,
    energyInferred: false,
    forceInferred: false,
  };
}
