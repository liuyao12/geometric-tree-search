export const CENTROSYMMETRY_PROVENANCE = Object.freeze({
  title: "Dislocation nucleation and defect structure during surface indentation",
  authors: "C. L. Kelchner, S. J. Plimpton, and J. C. Hamilton",
  journal: "Physical Review B 58, 11085 (1998)",
  doi: "10.1103/PhysRevB.58.11085",
  url: "https://doi.org/10.1103/PhysRevB.58.11085",
});

const DEFAULT_BINS = 24;
const ALLOWED_NEIGHBORS = Object.freeze({ 2: [4, 6], 3: [6, 8, 12] });

function finiteVector(vector) {
  return Array.isArray(vector) && vector.length === 3
    && vector.every(Number.isFinite) && vector.some((value) => Math.abs(value) > 1e-12);
}

function squaredLength(vector) {
  return vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2;
}

function pairCost(first, second) {
  return (first[0] + second[0]) ** 2
    + (first[1] + second[1]) ** 2
    + (first[2] + second[2]) ** 2;
}

function compareVectors(first, second) {
  return squaredLength(first.vector) - squaredLength(second.vector)
    || first.vector[0] - second.vector[0]
    || first.vector[1] - second.vector[1]
    || first.vector[2] - second.vector[2]
    || first.index - second.index;
}

/**
 * Exact minimum-weight perfect pairing of a fixed nearest-neighbor shell.
 * Kelchner et al.'s centrosymmetry parameter is the sum |r_i+r_j|^2 over
 * opposite-neighbor pairs.  We divide by sum |r_i|^2 to remove uniform scale,
 * and expose sqrt(P/(2 sum |r_i|^2)) as a bounded [0,1] asymmetry amplitude.
 */
export function optimalCentrosymmetryPairing(vectors, { neighborCount = 6 } = {}) {
  if (!Array.isArray(vectors)) throw new Error("centrosymmetry requires neighbor vectors");
  if (!Number.isInteger(neighborCount) || neighborCount < 2 || neighborCount > 12 || neighborCount % 2) {
    throw new Error("centrosymmetry neighbor count must be an even integer from 2 through 12");
  }
  if (vectors.some((vector) => !finiteVector(vector))) {
    throw new Error("centrosymmetry vectors must be finite non-zero Cartesian triples");
  }
  if (vectors.length < neighborCount) {
    return {
      resolved: false,
      reason: `requires ${neighborCount} neighbors; observed ${vectors.length}`,
      neighborCount,
      observedNeighbors: vectors.length,
      selectedNeighborIndices: [],
      pairs: [],
      rawParameter: null,
      normalizedParameter: null,
      normalizedAmplitude: null,
    };
  }

  const selected = vectors.map((vector, index) => ({ vector: [...vector], index }))
    .sort(compareVectors).slice(0, neighborCount);
  const costs = Array.from({ length: neighborCount }, (_, first) =>
    Array.from({ length: neighborCount }, (_, second) => pairCost(selected[first].vector, selected[second].vector)));
  const memo = new Map();
  const solve = (mask) => {
    if (!mask) return { cost: 0, pairs: [] };
    if (memo.has(mask)) return memo.get(mask);
    let first = 0;
    while (!(mask & (1 << first))) first++;
    const remainder = mask & ~(1 << first);
    let best = null;
    for (let second = first + 1; second < neighborCount; second++) {
      if (!(remainder & (1 << second))) continue;
      const child = solve(remainder & ~(1 << second));
      const candidate = { cost: costs[first][second] + child.cost,
        pairs: [[first, second], ...child.pairs] };
      const candidateKey = candidate.pairs.flat().join(",");
      const bestKey = best?.pairs.flat().join(",") || "";
      if (!best || candidate.cost < best.cost - 1e-14
        || (Math.abs(candidate.cost - best.cost) <= 1e-14 && candidateKey < bestKey)) best = candidate;
    }
    memo.set(mask, best);
    return best;
  };
  const solution = solve((1 << neighborCount) - 1);
  const denominator = selected.reduce((sum, entry) => sum + squaredLength(entry.vector), 0);
  const normalizedParameter = denominator > 1e-18 ? solution.cost / denominator : 0;
  return {
    resolved: true,
    reason: null,
    neighborCount,
    observedNeighbors: vectors.length,
    selectedNeighborIndices: selected.map((entry) => entry.index),
    pairs: solution.pairs.map(([first, second]) => ({
      firstNeighborIndex: selected[first].index,
      secondNeighborIndex: selected[second].index,
      pairCost: costs[first][second],
    })),
    rawParameter: solution.cost,
    shellSquaredRadius: denominator,
    normalizedParameter,
    normalizedAmplitude: Math.min(1, Math.sqrt(Math.max(0, normalizedParameter / 2))),
    pairingStatesEvaluated: memo.size,
  };
}

export function inferCentrosymmetryNeighborCount(neighborCounts, dimension = 3) {
  if (!Array.isArray(neighborCounts) || neighborCounts.some((value) => !Number.isInteger(value) || value < 0)) {
    throw new Error("centrosymmetry shell inference requires non-negative integer neighbor counts");
  }
  if (!ALLOWED_NEIGHBORS[dimension]) throw new Error("centrosymmetry supports intrinsic dimension 2 or 3");
  const candidates = ALLOWED_NEIGHBORS[dimension].map((neighborCount) => ({
    neighborCount,
    exactSupport: neighborCounts.filter((value) => value === neighborCount).length,
    resolvableSupport: neighborCounts.filter((value) => value >= neighborCount).length,
  }));
  const selected = [...candidates].sort((first, second) =>
    second.exactSupport - first.exactSupport
    || second.resolvableSupport - first.resolvableSupport
    || second.neighborCount - first.neighborCount)[0];
  return { dimension, selectedNeighborCount: selected.neighborCount, candidates };
}

export function localCentrosymmetry(neighborVectorsByCenter, { neighborCount = 6, bins = DEFAULT_BINS } = {}) {
  if (!Array.isArray(neighborVectorsByCenter)) throw new Error("centrosymmetry requires one shell per center");
  if (!Number.isInteger(bins) || bins < 2) throw new Error("centrosymmetry distribution requires at least two bins");
  const records = neighborVectorsByCenter.map((vectors, centerIndex) => ({
    centerIndex,
    ...optimalCentrosymmetryPairing(vectors, { neighborCount }),
  }));
  const resolved = records.filter((record) => record.resolved);
  const values = resolved.map((record) => record.normalizedAmplitude);
  const histogram = new Array(bins).fill(0);
  values.forEach((value) => { histogram[Math.min(bins - 1, Math.floor(value * bins))]++; });
  if (values.length) histogram.forEach((value, index) => { histogram[index] = value / values.length; });
  const sorted = [...values].sort((first, second) => first - second);
  const quantile = (fraction) => sorted.length
    ? sorted[Math.min(sorted.length - 1, Math.floor(fraction * (sorted.length - 1)))] : 0;
  return {
    neighborCount,
    records,
    values,
    histogram,
    bins,
    resolvedCenters: resolved.length,
    unresolvedCenters: records.length - resolved.length,
    resolvedFraction: resolved.length / Math.max(1, records.length),
    meanAmplitude: values.reduce((sum, value) => sum + value, 0) / Math.max(1, values.length),
    medianAmplitude: quantile(.5),
    percentile90Amplitude: quantile(.9),
    highAsymmetryFraction: values.filter((value) => value >= .25).length / Math.max(1, values.length),
    exactOptimalPairing: true,
    uniformScaleInvariant: true,
    translationInvariant: true,
    properRotationInvariant: true,
    atomPermutationInvariant: true,
    provenance: CENTROSYMMETRY_PROVENANCE,
  };
}
