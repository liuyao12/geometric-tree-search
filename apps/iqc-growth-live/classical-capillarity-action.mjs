import { cartesianNormalToIntrinsic, orientedEnergyKernelEstimate }
  from "./wulff-shape-regularizer.mjs";

const EPS = 1e-12;
const ANGSTROM_TO_METRE = 1e-10;
const ELECTRON_VOLT_JOULE = 1.602176634e-19;

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
  const normalized = basis.map((entry, index) => normalize(vector(entry, 3,
    `basis ${index + 1}`), `basis ${index + 1}`));
  for (let first = 0; first < dimension; first += 1) {
    for (let second = first + 1; second < dimension; second += 1) {
      if (Math.abs(dot(normalized[first], normalized[second])) > 1e-7) {
        throw new Error("orientation basis must be orthonormal");
      }
    }
  }
  return normalized;
}

function validateOrientations(orientations, dimension) {
  if (!Array.isArray(orientations) || orientations.length < dimension + 1) {
    throw new Error(`at least ${dimension + 1} oriented energies are required`);
  }
  return orientations.map((entry, index) => ({
    orientationId: String(entry.orientationId ?? `orientation-${index + 1}`),
    normal: normalize(vector(entry.normal, dimension, `orientation ${index + 1} normal`),
      `orientation ${index + 1} normal`),
    interfacialFreeEnergy: finite(entry.interfacialFreeEnergy,
      `orientation ${index + 1} interfacial energy`),
  })).map((entry) => {
    if (!(entry.interfacialFreeEnergy > 0)) throw new RangeError("interfacial energies must be positive");
    return entry;
  });
}

function worldNormal(intrinsicNormal, basis) {
  return basis[0].map((_, axis) => intrinsicNormal.reduce((sum, value, index) =>
    sum + value * basis[index][axis], 0));
}

function support(points, normal) {
  return Math.max(...points.map((point) => dot(point, normal)));
}

function workAtScale(nucleationWork, scaleMetre) {
  const dimension = nucleationWork.intrinsicDimension;
  const interfacial = nucleationWork.interfacialCoefficient * scaleMetre ** (dimension - 1);
  const bulk = nucleationWork.bulkDrivingFreeEnergyDensity
    * nucleationWork.normalizedWulffContent * scaleMetre ** dimension;
  return { interfacialJoule: interfacial, bulkGainJoule: bulk, workJoule: interfacial - bulk };
}

export function evaluateClassicalCapillarityAction({ occupiedPositionsAngstrom,
  emittedPositionsAngstrom, orientationBasisCartesian, orientations,
  maximumAngleRadians, nucleationWork }) {
  if (!nucleationWork?.conditionalClassicalModel || nucleationWork?.targetUsed) {
    throw new Error("accepted target-blind conditional nucleation work is required");
  }
  const dimension = Number(nucleationWork.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsic dimension must be 2 or 3");
  const basis = validateBasis(orientationBasisCartesian, dimension);
  const records = validateOrientations(orientations, dimension);
  const occupied = (occupiedPositionsAngstrom || []).map((entry, index) =>
    vector(entry, 3, `occupied position ${index + 1}`));
  const emitted = (emittedPositionsAngstrom || []).map((entry, index) =>
    vector(entry, 3, `emitted position ${index + 1}`));
  if (occupied.length < dimension + 1) return { available: false, supported: false,
    reason: "too few occupied sites to fit a finite Wulff scale", score: 0, targetUsed: false };
  if (!emitted.length) return { available: false, supported: false,
    reason: "candidate emits no novel sites", score: 0, targetUsed: false };
  const gammaMinimum = Math.min(...records.map((entry) => entry.interfacialFreeEnergy));
  const normalizedSupports = records.map((entry) => entry.interfacialFreeEnergy / gammaMinimum);
  const normalsWorld = records.map((entry) => worldNormal(entry.normal, basis));
  const beforeSupports = normalsWorld.map((normal) => support(occupied, normal));
  const rows = records.map((entry, index) => [...entry.normal, normalizedSupports[index]]);
  const beforeFit = leastSquares(rows, beforeSupports);
  if (!beforeFit || !(beforeFit[dimension] > EPS)) return { available: true, supported: false,
    reason: "occupied support does not admit a positive translated Wulff scale",
    score: 0, targetUsed: false };
  const translationIntrinsicAngstrom = beforeFit.slice(0, dimension);
  const beforeScaleAngstrom = beforeFit[dimension];
  const centerCartesianAngstrom = basis[0].map((_, axis) =>
    translationIntrinsicAngstrom.reduce((sum, value, index) => sum + value * basis[index][axis], 0));
  const emittedCentroid = emitted[0].map((_, axis) => emitted.reduce((sum, point) =>
    sum + point[axis], 0) / emitted.length);
  const outward = emittedCentroid.map((value, axis) => value - centerCartesianAngstrom[axis]);
  let candidateNormalIntrinsic;
  try { candidateNormalIntrinsic = cartesianNormalToIntrinsic(outward, basis); }
  catch { candidateNormalIntrinsic = null; }
  if (!candidateNormalIntrinsic) return { available: true, supported: false,
    reason: "candidate outward direction is unresolved in the intrinsic specimen frame",
    score: 0, beforeScaleAngstrom, targetUsed: false };
  const interpolation = orientedEnergyKernelEstimate(records, candidateNormalIntrinsic,
    finite(maximumAngleRadians, "maximum angle"));
  if (!interpolation.supported) return { available: true, supported: false,
    reason: interpolation.reason, score: 0, beforeScaleAngstrom,
    candidateNormalIntrinsic, interpolation, targetUsed: false };
  const afterSupports = normalsWorld.map((normal, index) => Math.max(beforeSupports[index],
    support(emitted, normal)));
  const denominator = normalizedSupports.reduce((sum, value) => sum + value * value, 0);
  const afterScaleAngstrom = normalizedSupports.reduce((sum, normalizedSupport, index) => {
    const translatedSupport = afterSupports[index]
      - dot(records[index].normal, translationIntrinsicAngstrom);
    return sum + normalizedSupport * translatedSupport;
  }, 0) / denominator;
  if (!(afterScaleAngstrom + EPS >= beforeScaleAngstrom)) return { available: true,
    supported: false, reason: "frozen-center Wulff scale is not monotone for this action",
    score: 0, beforeScaleAngstrom, afterScaleAngstrom, targetUsed: false };
  const normalizedResidual = (supports, scale) => Math.sqrt(supports.reduce((sum, value, index) => {
    const predicted = dot(records[index].normal, translationIntrinsicAngstrom)
      + scale * normalizedSupports[index];
    return sum + (value - predicted) ** 2;
  }, 0) / supports.length) / scale;
  const beforeScaleMetre = beforeScaleAngstrom * ANGSTROM_TO_METRE;
  const afterScaleMetre = afterScaleAngstrom * ANGSTROM_TO_METRE;
  const before = workAtScale(nucleationWork, beforeScaleMetre);
  const after = workAtScale(nucleationWork, afterScaleMetre);
  const deltaWorkJoule = after.workJoule - before.workJoule;
  const surfacePowerDifference = afterScaleMetre ** (dimension - 1)
    - beforeScaleMetre ** (dimension - 1);
  const contentDifference = nucleationWork.normalizedWulffContent
    * (afterScaleMetre ** dimension - beforeScaleMetre ** dimension);
  const deltaWorkUncertaintyJoule = Math.hypot(
    nucleationWork.interfacialCoefficientUncertainty * surfacePowerDifference,
    nucleationWork.bulkDrivingFreeEnergyDensityUncertainty * contentDifference);
  const criticalScaleMetre = nucleationWork.criticalScaleMetre;
  const regime = beforeScaleMetre >= criticalScaleMetre ? "supercritical"
    : afterScaleMetre >= criticalScaleMetre ? "crosses-critical-scale" : "subcritical";
  return {
    available: true, supported: true,
    reason: "validated gamma and delta_g with finite frozen-center Wulff-scale advance",
    score: Math.tanh(-deltaWorkJoule / nucleationWork.barrierJoule),
    regime, beforeScaleAngstrom, afterScaleAngstrom,
    beforeScaleNanometre: beforeScaleMetre * 1e9, afterScaleNanometre: afterScaleMetre * 1e9,
    criticalScaleNanometre: criticalScaleMetre * 1e9,
    beforeWorkJoule: before.workJoule, afterWorkJoule: after.workJoule,
    deltaWorkJoule, deltaWorkElectronVolt: deltaWorkJoule / ELECTRON_VOLT_JOULE,
    deltaWorkUncertaintyJoule,
    deltaWorkUncertaintyElectronVolt: deltaWorkUncertaintyJoule / ELECTRON_VOLT_JOULE,
    beforeNormalizedSupportResidual: normalizedResidual(beforeSupports, beforeScaleAngstrom),
    afterNormalizedSupportResidual: normalizedResidual(afterSupports, afterScaleAngstrom),
    translationIntrinsicAngstrom, centerCartesianAngstrom,
    candidateNormalIntrinsic, interpolation,
    occupiedSiteCount: occupied.length, emittedSiteCount: emitted.length,
    scaleModel: "pre-action least-squares Wulff translation and scale; center frozen; nondecreasing post-action scale fit",
    workModel: "delta[C_gamma s^(d-1) - delta_g V_0 s^d] normalized by the validated barrier",
    coordinateUnit: "angstrom", candidateSetChanged: false, candidateGeometryChanged: false,
    hardAdmissionChanged: false, atomCountInferred: false, attachmentRateInferred: false,
    nucleationRateInferred: false, physicalTimeIntegrated: false, targetUsed: false,
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

export function matchedClassicalCapillarityRankingAudit(records) {
  const normalized = (records || []).map((record) => ({ candidateId: String(record.candidateId),
    baselineScore: finite(record.baselineScore, "baseline score"),
    regularizedScore: finite(record.regularizedScore, "regularized score"),
    supported: record.supported === true, deltaWorkJoule: record.deltaWorkJoule == null
      ? null : finite(record.deltaWorkJoule, "delta work") }));
  if (new Set(normalized.map((entry) => entry.candidateId)).size !== normalized.length) {
    throw new Error("candidate IDs must be unique for a matched ranking audit");
  }
  const baseline = ranked(normalized, "baselineScore");
  const regularized = ranked(normalized, "regularizedScore");
  const newRank = new Map(regularized.map((entry, index) => [entry.candidateId, index]));
  const permutation = baseline.map((entry) => newRank.get(entry.candidateId));
  const maximumInversions = normalized.length * (normalized.length - 1) / 2;
  const inversions = inversionCount(permutation);
  return { candidateCount: normalized.length,
    supportedCandidates: normalized.filter((entry) => entry.supported).length,
    abstainedCandidates: normalized.filter((entry) => !entry.supported).length,
    favorableCandidates: normalized.filter((entry) => entry.supported && entry.deltaWorkJoule < 0).length,
    unfavorableCandidates: normalized.filter((entry) => entry.supported && entry.deltaWorkJoule > 0).length,
    rankInversions: inversions, maximumRankInversions: maximumInversions,
    inversionFraction: maximumInversions ? inversions / maximumInversions : 0,
    leaderChanged: baseline[0]?.candidateId !== regularized[0]?.candidateId,
    baselineLeaderId: baseline[0]?.candidateId || null,
    regularizedLeaderId: regularized[0]?.candidateId || null,
    candidateSetIdentical: true, candidateGeometryChanged: false, hardAdmissionChanged: false,
    targetUsed: false };
}
