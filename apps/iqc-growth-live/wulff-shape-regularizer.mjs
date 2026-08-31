const EPS = 1e-10;

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function vector(value, dimension, label) {
  if (!Array.isArray(value) || value.length !== dimension) {
    throw new TypeError(`${label} must have ${dimension} components`);
  }
  return value.map((entry, index) => finite(entry, `${label}[${index}]`));
}

function dot(first, second) {
  return first.reduce((sum, value, index) => sum + value * second[index], 0);
}

function normalize(value, label) {
  const norm = Math.hypot(...value);
  if (!(norm > EPS)) throw new RangeError(`${label} must be nonzero`);
  return value.map((entry) => entry / norm);
}

function solveLinear(matrix, values) {
  const size = values.length;
  const rows = matrix.map((row, index) => [...row, values[index]]);
  for (let column = 0; column < size; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < size; row += 1) {
      if (Math.abs(rows[row][column]) > Math.abs(rows[pivot][column])) pivot = row;
    }
    if (Math.abs(rows[pivot][column]) <= EPS) return null;
    [rows[column], rows[pivot]] = [rows[pivot], rows[column]];
    const scale = rows[column][column];
    for (let entry = column; entry <= size; entry += 1) rows[column][entry] /= scale;
    for (let row = 0; row < size; row += 1) {
      if (row === column) continue;
      const factor = rows[row][column];
      for (let entry = column; entry <= size; entry += 1) rows[row][entry] -= factor * rows[column][entry];
    }
  }
  return rows.map((row) => row[size]);
}

function leastSquares(rows, values) {
  const columns = rows[0]?.length || 0;
  const gram = Array.from({ length: columns }, () => Array(columns).fill(0));
  const rhs = Array(columns).fill(0);
  rows.forEach((row, index) => row.forEach((value, first) => {
    rhs[first] += value * values[index];
    row.forEach((other, second) => { gram[first][second] += value * other; });
  }));
  return solveLinear(gram, rhs);
}

function validateBasis(basis, dimension) {
  if (!Array.isArray(basis) || basis.length !== dimension) {
    throw new TypeError(`orientation basis must contain ${dimension} Cartesian vectors`);
  }
  const result = basis.map((entry, index) => normalize(vector(entry, 3, `basis ${index + 1}`), `basis ${index + 1}`));
  for (let first = 0; first < dimension; first += 1) for (let second = first + 1; second < dimension; second += 1) {
    if (Math.abs(dot(result[first], result[second])) > 1e-7) throw new Error("orientation basis must be orthonormal");
  }
  return result;
}

function validateOrientations(orientations, dimension) {
  if (!Array.isArray(orientations) || orientations.length < dimension + 1) {
    throw new Error(`at least ${dimension + 1} oriented energies are required`);
  }
  return orientations.map((entry, index) => ({
    orientationId: String(entry.orientationId ?? `orientation-${index + 1}`),
    normal: normalize(vector(entry.normal, dimension, `orientation ${index + 1} normal`),
      `orientation ${index + 1} normal`),
    interfacialFreeEnergy: finite(entry.interfacialFreeEnergy, `orientation ${index + 1} energy`),
    uncertainty: finite(entry.uncertainty ?? 0, `orientation ${index + 1} uncertainty`),
  })).map((entry) => {
    if (!(entry.interfacialFreeEnergy > 0) || entry.uncertainty < 0) {
      throw new RangeError("interfacial energies must be positive and uncertainties nonnegative");
    }
    return entry;
  });
}

export function cartesianNormalToIntrinsic(cartesianNormal, orientationBasisCartesian) {
  const basis = validateBasis(orientationBasisCartesian, orientationBasisCartesian?.length);
  const cartesian = normalize(vector(cartesianNormal, 3, "Cartesian normal"), "Cartesian normal");
  const projection = basis.map((axis) => dot(cartesian, axis));
  const projectionNorm = Math.hypot(...projection);
  if (!(projectionNorm > 1e-7)) return null;
  return projection.map((value) => value / projectionNorm);
}

export function orientedEnergyKernelEstimate(orientations, orientedNormal, maximumAngleRadians) {
  const dimension = orientedNormal?.length;
  const records = validateOrientations(orientations, dimension);
  const normal = normalize(vector(orientedNormal, dimension, "query normal"), "query normal");
  const maximumAngle = finite(maximumAngleRadians, "maximum angle");
  if (!(maximumAngle > 0 && maximumAngle <= Math.PI)) throw new RangeError("maximum angle must lie in (0, pi]");
  const neighbors = records.map((entry) => ({ entry,
    angle: Math.acos(Math.max(-1, Math.min(1, dot(normal, entry.normal)))) }))
    .filter(({ angle }) => angle <= maximumAngle + EPS)
    .sort((first, second) => first.angle - second.angle
      || first.entry.orientationId.localeCompare(second.entry.orientationId));
  if (!neighbors.length) return { supported: false, reason: "no oriented energy within angular reach",
    maximumAngleRadians: maximumAngle, nearestAngleRadians: null, neighborCount: 0,
    targetUsed: false, inversionSymmetrized: false };
  if (neighbors[0].angle <= EPS) return { supported: true, reason: "exact supplied orientation",
    interfacialFreeEnergy: neighbors[0].entry.interfacialFreeEnergy,
    uncertainty: neighbors[0].entry.uncertainty,
    maximumAngleRadians: maximumAngle, nearestAngleRadians: 0, neighborCount: 1,
    orientationIds: [neighbors[0].entry.orientationId], targetUsed: false, inversionSymmetrized: false };
  const weighted = neighbors.map(({ entry, angle }) => ({ entry, angle,
    weight: Math.max(0, 1 - angle / maximumAngle) ** 2 }));
  const total = weighted.reduce((sum, record) => sum + record.weight, 0);
  if (!(total > EPS)) return { supported: false, reason: "only zero-weight angular boundary samples",
    maximumAngleRadians: maximumAngle, nearestAngleRadians: neighbors[0].angle,
    neighborCount: neighbors.length, targetUsed: false, inversionSymmetrized: false };
  const normalizedWeights = weighted.map((record) => record.weight / total);
  return {
    supported: true, reason: "finite oriented angular kernel",
    interfacialFreeEnergy: normalizedWeights.reduce((sum, weight, index) =>
      sum + weight * weighted[index].entry.interfacialFreeEnergy, 0),
    uncertainty: Math.sqrt(normalizedWeights.reduce((sum, weight, index) =>
      sum + (weight * weighted[index].entry.uncertainty) ** 2, 0)),
    maximumAngleRadians: maximumAngle, nearestAngleRadians: neighbors[0].angle,
    neighborCount: neighbors.length,
    orientationIds: weighted.map((record) => record.entry.orientationId),
    targetUsed: false, inversionSymmetrized: false,
  };
}

function worldNormal(intrinsicNormal, basis) {
  return basis[0].map((_, axis) => intrinsicNormal.reduce((sum, value, index) =>
    sum + value * basis[index][axis], 0));
}

function support(points, normal) {
  return Math.max(...points.map((point) => dot(point, normal)));
}

export function evaluateWulffShapeRegularizer({ occupiedPositions, emittedPositions,
  orientationBasisCartesian, orientations, maximumAngleRadians }) {
  const dimension = orientationBasisCartesian?.length;
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsic dimension must be 2 or 3");
  const basis = validateBasis(orientationBasisCartesian, dimension);
  const records = validateOrientations(orientations, dimension);
  const occupied = (occupiedPositions || []).map((entry, index) => vector(entry, 3, `occupied position ${index + 1}`));
  const emitted = (emittedPositions || []).map((entry, index) => vector(entry, 3, `emitted position ${index + 1}`));
  if (occupied.length < dimension + 1) return { available: false, supported: false,
    reason: "too few occupied sites to fit a finite Wulff support", score: 0, targetUsed: false };
  if (!emitted.length) return { available: false, supported: false,
    reason: "candidate emits no novel sites", score: 0, targetUsed: false };
  const gammaMinimum = Math.min(...records.map((entry) => entry.interfacialFreeEnergy));
  const rows = records.map((entry) => [...entry.normal, entry.interfacialFreeEnergy / gammaMinimum]);
  const normalsWorld = records.map((entry) => worldNormal(entry.normal, basis));
  const beforeSupports = normalsWorld.map((normal) => support(occupied, normal));
  const fit = leastSquares(rows, beforeSupports);
  if (!fit || !(fit[dimension] > EPS)) return { available: false, supported: false,
    reason: "occupied support does not admit a positive translated Wulff scale", score: 0, targetUsed: false };
  const translationIntrinsic = fit.slice(0, dimension); const scale = fit[dimension];
  const centerCartesian = basis[0].map((_, axis) => translationIntrinsic.reduce((sum, value, index) =>
    sum + value * basis[index][axis], 0));
  const emittedCentroid = emitted[0].map((_, axis) => emitted.reduce((sum, point) => sum + point[axis], 0) / emitted.length);
  const candidateNormalCartesian = emittedCentroid.map((value, axis) => value - centerCartesian[axis]);
  let candidateNormalIntrinsic;
  try { candidateNormalIntrinsic = cartesianNormalToIntrinsic(candidateNormalCartesian, basis); }
  catch { candidateNormalIntrinsic = null; }
  if (!candidateNormalIntrinsic) return { available: true, supported: false,
    reason: "candidate outward direction is unresolved in the intrinsic specimen frame",
    score: 0, scale, translationIntrinsic, centerCartesian, targetUsed: false };
  const interpolation = orientedEnergyKernelEstimate(records, candidateNormalIntrinsic, maximumAngleRadians);
  if (!interpolation.supported) return { available: true, supported: false,
    reason: interpolation.reason, score: 0, scale, translationIntrinsic, centerCartesian,
    candidateNormalCartesian: normalize(candidateNormalCartesian, "candidate normal"),
    candidateNormalIntrinsic, interpolation, targetUsed: false };
  const predicted = rows.map((row) => dot(row, fit));
  const afterSupports = normalsWorld.map((normal, index) => Math.max(beforeSupports[index], support(emitted, normal)));
  const squaredError = (supports) => supports.reduce((sum, value, index) =>
    sum + ((value - predicted[index]) / scale) ** 2, 0) / supports.length;
  const mismatchBefore = squaredError(beforeSupports); const mismatchAfter = squaredError(afterSupports);
  const mismatchImprovement = mismatchBefore - mismatchAfter;
  return {
    available: true, supported: true, reason: "validated orientation coverage and positive finite-nucleus fit",
    score: Math.tanh(4 * mismatchImprovement), mismatchBefore, mismatchAfter, mismatchImprovement,
    scale, translationIntrinsic, centerCartesian,
    candidateNormalCartesian: normalize(candidateNormalCartesian, "candidate normal"),
    candidateNormalIntrinsic, interpolation,
    fittedOrientationCount: records.length, occupiedSiteCount: occupied.length, emittedSiteCount: emitted.length,
    fitModel: "least-squares translated support h(n)=n·t+lambda gamma(n)/gamma_min; lambda frozen before candidate",
    candidateSetChanged: false, candidateGeometryChanged: false, hardAdmissionChanged: false,
    usedAsAttachmentRate: false, usedAsGrowthLaw: false, targetUsed: false,
  };
}

function ranked(records, key) {
  return [...records].sort((first, second) => second[key] - first[key]
    || String(first.candidateId).localeCompare(String(second.candidateId)));
}

function inversionCount(permutation) {
  const tree = Array(permutation.length + 1).fill(0); let inversions = 0;
  const add = (index) => { for (let cursor = index + 1; cursor < tree.length; cursor += cursor & -cursor) tree[cursor] += 1; };
  const sum = (index) => { let total = 0; for (let cursor = index + 1; cursor > 0; cursor -= cursor & -cursor) total += tree[cursor]; return total; };
  permutation.forEach((value, index) => { inversions += index - sum(value); add(value); });
  return inversions;
}

export function matchedWulffRankingAudit(records) {
  const normalized = (records || []).map((record) => ({ candidateId: String(record.candidateId),
    baselineScore: finite(record.baselineScore, "baseline score"),
    regularizedScore: finite(record.regularizedScore, "regularized score"),
    supported: record.supported === true }));
  if (new Set(normalized.map((entry) => entry.candidateId)).size !== normalized.length) {
    throw new Error("candidate IDs must be unique for a matched ranking audit");
  }
  const baseline = ranked(normalized, "baselineScore"); const regularized = ranked(normalized, "regularizedScore");
  const newRank = new Map(regularized.map((entry, index) => [entry.candidateId, index]));
  const permutation = baseline.map((entry) => newRank.get(entry.candidateId));
  const maximumInversions = normalized.length * (normalized.length - 1) / 2;
  const inversions = inversionCount(permutation);
  return {
    candidateCount: normalized.length, supportedCandidates: normalized.filter((entry) => entry.supported).length,
    abstainedCandidates: normalized.filter((entry) => !entry.supported).length,
    rankInversions: inversions, maximumRankInversions: maximumInversions,
    inversionFraction: maximumInversions ? inversions / maximumInversions : 0,
    leaderChanged: baseline[0]?.candidateId !== regularized[0]?.candidateId,
    baselineLeaderId: baseline[0]?.candidateId || null,
    regularizedLeaderId: regularized[0]?.candidateId || null,
    candidateSetIdentical: true, candidateGeometryChanged: false, hardAdmissionChanged: false,
    targetUsed: false,
  };
}
