function squaredDistance(first, second) {
  let total = 0;
  for (let axis = 0; axis < first.length; axis++) {
    const delta = first[axis] - second[axis]; total += delta * delta;
  }
  return total;
}

function quantile(values, fraction) {
  if (!values.length) return null;
  const sorted = [...values].sort((first, second) => first - second);
  const position = Math.max(0, Math.min(sorted.length - 1, fraction * (sorted.length - 1)));
  const lower = Math.floor(position); const upper = Math.ceil(position);
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function centroid(positions) {
  const center = new Array(positions[0]?.length || 3).fill(0);
  positions.forEach((point) => point.forEach((value, axis) => { center[axis] += value / positions.length; }));
  return center;
}

function determinant3(matrix) {
  return matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
    - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
    + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
}

function solveLinear(matrix, values) {
  if (matrix.length === 2) {
    const determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
    if (Math.abs(determinant) < 1e-11) return null;
    return [(values[0] * matrix[1][1] - matrix[0][1] * values[1]) / determinant,
      (matrix[0][0] * values[1] - values[0] * matrix[1][0]) / determinant];
  }
  const determinant = determinant3(matrix);
  if (Math.abs(determinant) < 1e-11) return null;
  return [0, 1, 2].map((column) => {
    const replaced = matrix.map((row, rowIndex) => row.map((value, columnIndex) =>
      columnIndex === column ? values[rowIndex] : value));
    return determinant3(replaced) / determinant;
  });
}

function combinations(values, size, start = 0, prefix = [], result = []) {
  if (prefix.length === size) { result.push(prefix); return result; }
  for (let index = start; index <= values.length - (size - prefix.length); index++) {
    combinations(values, size, index + 1, [...prefix, values[index]], result);
  }
  return result;
}

function canonicalAnchors(positions, maximumAnchors) {
  if (positions.length <= maximumAnchors) return positions.map((_, index) => index);
  const center = centroid(positions);
  const records = positions.map((point, index) => ({ index, radius2: squaredDistance(point, center),
    fingerprint: positions.map((other, otherIndex) => otherIndex === index ? 0 : squaredDistance(point, other))
      .sort((first, second) => first - second) }));
  records.sort((first, second) => {
    if (first.radius2 !== second.radius2) return first.radius2 - second.radius2;
    for (let index = 0; index < first.fingerprint.length; index++) {
      if (first.fingerprint[index] !== second.fingerprint[index]) {
        return first.fingerprint[index] - second.fingerprint[index];
      }
    }
    return 0;
  });
  return Array.from({ length: maximumAnchors }, (_, sample) => records[Math.min(records.length - 1,
    Math.floor((sample + .5) * records.length / maximumAnchors))].index);
}

function referenceNearestNeighborScale(positions, maximumAnchors) {
  const distances = canonicalAnchors(positions, maximumAnchors).map((index) => Math.sqrt(Math.min(
    ...positions.map((point, other) => other === index ? Infinity : squaredDistance(positions[index], point)))));
  return quantile(distances.filter(Number.isFinite), .5);
}

function simplexCircumcenter(vertices) {
  const origin = vertices[0];
  const edges = vertices.slice(1).map((point) => point.map((value, axis) => value - origin[axis]));
  const gram = edges.map((first) => edges.map((second) => first.reduce((sum, value, axis) => sum + value * second[axis], 0)));
  const weights = solveLinear(gram, edges.map((edge) => squaredDistance(edge, new Array(edge.length).fill(0)) / 2));
  if (!weights) return null;
  const offset = origin.map((_, axis) => edges.reduce((sum, edge, index) => sum + weights[index] * edge[axis], 0));
  const center = origin.map((value, axis) => value + offset[axis]);
  const barycentric = [1 - weights.reduce((sum, value) => sum + value, 0), ...weights];
  if (barycentric.some((weight) => weight < -1e-8 || weight > 1 + 1e-8)) return null;
  return center;
}

function witnessedEmptyCenters(positions, dimension, maximumAnchors, neighborLimit) {
  const candidates = [];
  canonicalAnchors(positions, maximumAnchors).forEach((anchor) => {
    const ordered = positions.map((point, index) => ({ index, distance2: index === anchor
      ? Infinity : squaredDistance(positions[anchor], point) })).sort((first, second) => first.distance2 - second.distance2);
    const finite = ordered.filter((record) => Number.isFinite(record.distance2));
    const cutoff = finite[Math.min(neighborLimit - 1, finite.length - 1)]?.distance2 ?? Infinity;
    const neighbors = finite.filter((record) => record.distance2 <= cutoff * (1 + 1e-10) + 1e-12)
      .map((record) => record.index);
    combinations(neighbors, dimension).forEach((others) => {
      const vertices = [anchor, ...others];
      const center = simplexCircumcenter(vertices.map((index) => positions[index]));
      if (!center) return;
      const radius2 = squaredDistance(center, positions[anchor]);
      const minimumDistance2 = Math.min(...positions.map((point) => squaredDistance(center, point)));
      if (minimumDistance2 + 1e-9 < radius2) return;
      candidates.push({ center, clearance: Math.sqrt(minimumDistance2), vertices: [...vertices].sort((a, b) => a - b) });
    });
  });
  const parents = candidates.map((_, index) => index);
  const root = (index) => { while (parents[index] !== index) { parents[index] = parents[parents[index]]; index = parents[index]; } return index; };
  const unite = (first, second) => { const a = root(first); const b = root(second); if (a !== b) parents[Math.max(a, b)] = Math.min(a, b); };
  const tolerance = 1e-6;
  const neighborOffsets = [];
  const buildOffsets = (prefix = []) => {
    if (prefix.length === dimension) { neighborOffsets.push(prefix); return; }
    [-1, 0, 1].forEach((value) => buildOffsets([...prefix, value]));
  };
  buildOffsets();
  const cells = new Map();
  candidates.forEach((candidate, index) => {
    const cell = candidate.center.map((value) => Math.floor(value / tolerance));
    neighborOffsets.forEach((offset) => {
      const key = cell.map((value, axis) => value + offset[axis]).join(",");
      (cells.get(key) || []).forEach((other) => {
        if (squaredDistance(candidate.center, candidates[other].center) <= tolerance * tolerance) unite(index, other);
      });
    });
    const key = cell.join(","); if (!cells.has(key)) cells.set(key, []); cells.get(key).push(index);
  });
  const components = new Map();
  candidates.forEach((candidate, index) => {
    const key = root(index); if (!components.has(key)) components.set(key, []); components.get(key).push(candidate);
  });
  return [...components.values()].map((records) => ({
    center: records[0].center.map((_, axis) => records.reduce((sum, record) => sum + record.center[axis], 0) / records.length),
    clearance: records.reduce((sum, record) => sum + record.clearance, 0) / records.length,
  })).sort((first, second) => first.clearance - second.clearance);
}

function summarize(positions, dimension, maximumAnchors, neighborLimit, histogramBins, histogramMaximum) {
  const centers = witnessedEmptyCenters(positions, dimension, maximumAnchors, neighborLimit);
  const structureCenter = centroid(positions);
  const maximumStructureRadius = Math.max(1e-12, ...positions.map((point) => Math.sqrt(squaredDistance(point, structureCenter))));
  const records = centers.map((record) => ({ clearance: record.clearance,
    normalizedRadius: Math.sqrt(squaredDistance(record.center, structureCenter)) / maximumStructureRadius }));
  const clearances = records.map((record) => record.clearance);
  const core = records.filter((record) => record.normalizedRadius <= .5).map((record) => record.clearance);
  const front = records.filter((record) => record.normalizedRadius >= .75).map((record) => record.clearance);
  const histogram = new Array(histogramBins).fill(0);
  clearances.forEach((clearance) => { histogram[Math.min(histogramBins - 1,
    Math.max(0, Math.floor(clearance / histogramMaximum * histogramBins)))]++; });
  return {
    candidateCenters: records.length,
    medianClearance: quantile(clearances, .5),
    percentile90Clearance: quantile(clearances, .9),
    maximumClearance: clearances.length ? Math.max(...clearances) : null,
    coreMedianClearance: quantile(core, .5),
    frontMedianClearance: quantile(front, .5),
    radialRecords: records,
    histogram,
  };
}

export function interstitialClearanceAudit(currentPositions, referencePositions, {
  dimension = 3, maximumAnchors = 64, neighborLimit = 6, histogramBins = 20,
  histogramMaximum = 1.5,
} = {}) {
  const resolvedDimension = dimension === 2 ? 2 : 3;
  const minimumSites = resolvedDimension + 2;
  if (currentPositions.length < minimumSites || referencePositions.length < minimumSites) return {
    available: false, reason: `at least ${minimumSites} current and reference sites are required`,
    dimension: resolvedDimension, targetUsed: false,
  };
  const referenceScale = referenceNearestNeighborScale(referencePositions, maximumAnchors);
  if (!Number.isFinite(referenceScale) || referenceScale <= 1e-12) return {
    available: false, reason: "a positive supplied nearest-neighbor scale is required",
    dimension: resolvedDimension, targetUsed: false,
  };
  const normalize = (positions) => positions.map((point) => point.map((value) => value / referenceScale));
  const current = summarize(normalize(currentPositions), resolvedDimension, maximumAnchors,
    neighborLimit, histogramBins, histogramMaximum);
  const reference = summarize(normalize(referencePositions), resolvedDimension, maximumAnchors,
    neighborLimit, histogramBins, histogramMaximum);
  if (!current.candidateCenters || !reference.candidateCenters) return {
    available: false, reason: "no nondegenerate locally witnessed empty simplex centers were resolved",
    dimension: resolvedDimension, currentCandidateCenters: current.candidateCenters,
    referenceCandidateCenters: reference.candidateCenters, targetUsed: false,
  };
  return {
    available: true,
    dimension: resolvedDimension,
    currentSites: currentPositions.length,
    referenceSites: referencePositions.length,
    referenceNearestNeighborScale: referenceScale,
    maximumAnchors,
    neighborLimit,
    histogramBins,
    histogramMaximum,
    histogramOverflowIncludedInLastBin: true,
    ...current,
    reference,
    clearanceDefinition: "empty circumcircle/circumsphere center clearance divided by supplied median nearest-neighbor distance",
    candidateDefinition: "nondegenerate local simplices from an invariant radial anchor sample and its nearest-neighbor tie set; center retained only inside the simplex and empty of explicit sites",
    finiteObservationNoPeriodicImages: true,
    pointSitesNoAtomicRadii: true,
    translationInvariant: true,
    properRotationInvariant: true,
    atomPermutationInvariant: true,
    uniformScaleInvariantWhenCurrentAndReferenceShareScale: true,
    targetUsed: false,
    usedAsGrowthInput: false,
    porosityInferred: false,
    poreVolumeInferred: false,
    accessibleFreeVolumeInferred: false,
    vacancyOrInterstitialIdentityInferred: false,
    diffusionPathInferred: false,
    migrationBarrierInferred: false,
    pressureInferred: false,
    physicalTimeIntegrated: false,
  };
}
