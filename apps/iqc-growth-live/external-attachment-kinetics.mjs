import { buildNormalizedWulffGeometry } from "./external-interfacial-energy.mjs";
import { cartesianNormalToIntrinsic, orientedEnergyKernelEstimate,
  matchedWulffRankingAudit } from "./wulff-shape-regularizer.mjs";

export const ATTACHMENT_KINETICS_REQUEST_SCHEMA = "gcts-oriented-attachment-kinetics-request-v1";
export const ATTACHMENT_KINETICS_RESPONSE_SCHEMA = "gcts-oriented-attachment-kinetics-response-v1";

const EPS = 1e-10;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function positive(value, label) {
  const number = finite(value, label);
  if (!(number > 0)) throw new RangeError(`${label} must be positive`);
  return number;
}

function digest(value, label) {
  const text = requiredText(value, label).toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(text)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return text;
}

function dot(first, second) {
  return first.reduce((sum, value, index) => sum + value * second[index], 0);
}

function normalized(value, label) {
  if (!Array.isArray(value)) throw new TypeError(`${label} must be an array`);
  const result = value.map((entry, index) => finite(entry, `${label}[${index}]`));
  const norm = Math.hypot(...result);
  if (!(norm > EPS)) throw new RangeError(`${label} must be nonzero`);
  return result.map((entry) => entry / norm);
}

function basis(value, dimension) {
  if (!Array.isArray(value) || value.length !== dimension) {
    throw new TypeError(`orientation basis must contain ${dimension} vectors`);
  }
  const result = value.map((entry, index) => {
    if (!Array.isArray(entry) || entry.length !== 3) throw new TypeError(`basis ${index + 1} must have 3 components`);
    return normalized(entry, `basis ${index + 1}`);
  });
  for (let first = 0; first < dimension; first += 1) for (let second = first + 1; second < dimension; second += 1) {
    if (Math.abs(dot(result[first], result[second])) > 1e-7) throw new Error("orientation basis must be orthonormal");
  }
  return result;
}

function sameBasis(first, second) {
  return first.length === second.length && first.every((row, index) =>
    row.every((value, axis) => Math.abs(value - second[index][axis]) <= 1e-9));
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonical(value[key])]));
  return value;
}

export async function attachmentKineticsSha256(value) {
  const bytes = new TextEncoder().encode(typeof value === "string" ? value : JSON.stringify(canonical(value)));
  const hash = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(hash)].map((entry) => entry.toString(16).padStart(2, "0")).join("");
}

export function buildAttachmentKineticsRequest(input) {
  if (input?.targetUsed === true || input?.targetCoordinatesEmbedded === true) {
    throw new Error("an attachment-kinetics request cannot use a growth target");
  }
  const intrinsicDimension = Number(input?.intrinsicDimension);
  if (![2, 3].includes(intrinsicDimension)) throw new RangeError("intrinsicDimension must be 2 or 3");
  const orientationBasisCartesian = basis(input.orientationBasisCartesian, intrinsicDimension);
  const structureSha256 = digest(input.structureSha256, "structure SHA-256");
  return {
    schema: ATTACHMENT_KINETICS_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId), materialName: requiredText(input.materialName, "material name"),
      elements: [...new Set((input.elements || []).map(String))].sort(), structureSha256,
      intrinsicDimension, orientationBasisCartesian,
      orientationCoordinates: "normal components multiply the ordered Cartesian basis vectors",
      sourceProvenance: input.sourceProvenance || null, recordedConditions: input.recordedConditions || null,
    },
    calculation: {
      quantity: "orientation-resolved steady normal growth velocity at one declared driving condition",
      requiredOrientationConvention: "oriented unit outward normal in the supplied Cartesian specimen frame",
      suitableMethods: ["orientation-resolved interface-advance simulation",
        "phase-field or sharp-interface calibration against a resolved microscopic model",
        "orientation-resolved in-situ growth measurement"],
      requiredOutputs: ["one positive steady normal velocity and one-sigma uncertainty per oriented normal",
        "temperature and a complete driving-condition description/digest",
        "method, version, complete settings digest, convergence and steady-state declarations"],
      units: "metre per second", responseSchema: ATTACHMENT_KINETICS_RESPONSE_SCHEMA,
    },
    expectedResponse: {
      schema: ATTACHMENT_KINETICS_RESPONSE_SCHEMA, requestSha256: "SHA-256 of this complete request file",
      structureSha256, intrinsicDimension, orientationBasisCartesian,
      drivingCondition: { description: "required", settingsSha256: "64 hexadecimal characters",
        temperatureKelvin: "positive", couplingStateSha256: "optional shared transport/kinetics state digest" },
      method: { family: "required", program: "required", version: "declared or null",
        settingsSha256: "64 hexadecimal characters" },
      orientations: [{ orientationId: "unique", normal: `array[${intrinsicDimension}]`,
        normalGrowthVelocity: "finite positive metre per second", uncertainty: "finite nonnegative" }],
    },
    safeguards: {
      requestOnly: true, targetCoordinatesEmbedded: false, targetUsedForSelection: false,
      morphologyUsedToInferVelocity: false, interfacialFreeEnergyUsedAsVelocity: false,
      orientedNormalsNotSilentlyInversionSymmetrized: true,
      responseMayOnlyRankTheUnchangedExactCandidateSetAfterExplicitOptIn: true,
      actionBarrierOrAttachmentProbabilityInferred: false, physicalTimeIntegrated: false,
    },
  };
}

export function buildNormalizedKineticWulffGeometry(orientations, intrinsicDimension) {
  if (!Array.isArray(orientations)) throw new TypeError("orientations must be an array");
  const mapped = orientations.map((entry, index) => {
    const normalGrowthVelocity = positive(entry.normalGrowthVelocity,
      `orientation ${index + 1} normal velocity`);
    return { orientationId: requiredText(entry.orientationId, `orientation ${index + 1} ID`),
      normal: [...entry.normal], interfacialFreeEnergy: normalGrowthVelocity,
      uncertainty: finite(entry.uncertainty ?? 0, `orientation ${index + 1} uncertainty`) };
  });
  const geometry = buildNormalizedWulffGeometry(mapped, intrinsicDimension);
  return { ...geometry,
    normalization: "support distances divided by minimum supplied steady normal growth velocity",
    gammaMinimum: undefined, velocityMinimumMetrePerSecond: Math.min(...orientations.map((entry) => entry.normalGrowthVelocity)),
    equilibriumShapeConditionalOnSuppliedOrientations: false,
    kineticWulffShapeConditionalOnSuppliedOrientations: true,
    interfacialFreeEnergyUsed: false, physicalTimeIntegrated: false };
}

export function validateAttachmentKineticsResponse(response, expected) {
  if (response?.schema !== ATTACHMENT_KINETICS_RESPONSE_SCHEMA) throw new Error("unsupported attachment-kinetics response schema");
  const requestSha256 = digest(response.requestSha256, "response request SHA-256");
  const structureSha256 = digest(response.structureSha256, "response structure SHA-256");
  if (requestSha256 !== digest(expected.requestSha256, "expected request SHA-256")) throw new Error("response does not match the exact request");
  if (structureSha256 !== digest(expected.structureSha256, "expected structure SHA-256")) throw new Error("response does not match the exact specimen");
  const intrinsicDimension = Number(response.intrinsicDimension);
  if (intrinsicDimension !== Number(expected.intrinsicDimension) || ![2, 3].includes(intrinsicDimension)) {
    throw new Error("response intrinsic dimension mismatch");
  }
  const orientationBasisCartesian = basis(response.orientationBasisCartesian, intrinsicDimension);
  const expectedBasis = basis(expected.orientationBasisCartesian, intrinsicDimension);
  if (!sameBasis(orientationBasisCartesian, expectedBasis)) throw new Error("response orientation basis mismatch");
  if (response.units !== "metre per second") throw new Error("response units must be 'metre per second'");
  const method = { family: requiredText(response.method?.family, "method family"),
    program: requiredText(response.method?.program, "method program"),
    version: response.method?.version == null ? null : String(response.method.version),
    settingsSha256: digest(response.method?.settingsSha256, "method settings SHA-256") };
  const drivingCondition = {
    description: requiredText(response.drivingCondition?.description, "driving-condition description"),
    settingsSha256: digest(response.drivingCondition?.settingsSha256, "driving-condition settings SHA-256"),
    temperatureKelvin: positive(response.drivingCondition?.temperatureKelvin, "driving-condition temperature"),
    couplingStateSha256: response.drivingCondition?.couplingStateSha256 == null ? null
      : digest(response.drivingCondition.couplingStateSha256, "driving-condition coupling-state SHA-256"),
  };
  const validation = response.validation || {};
  for (const field of ["passed", "converged", "uncertaintyReported", "orientationSetPredeclared",
    "steadyStateWindowVerified"]) if (validation[field] !== true) throw new Error(`validation.${field} must be true`);
  if (!Array.isArray(response.orientations) || response.orientations.length < intrinsicDimension + 1) {
    throw new Error(`at least ${intrinsicDimension + 1} oriented velocities are required`);
  }
  const ids = new Set(); const normals = [];
  const orientations = response.orientations.map((entry, index) => {
    const orientationId = requiredText(entry?.orientationId, `orientation ${index + 1} ID`);
    if (ids.has(orientationId)) throw new Error(`duplicate orientation ID ${orientationId}`);
    ids.add(orientationId);
    if (!Array.isArray(entry.normal) || entry.normal.length !== intrinsicDimension) {
      throw new TypeError(`${orientationId} normal must have ${intrinsicDimension} components`);
    }
    const normal = normalized(entry.normal, `${orientationId} normal`);
    if (normals.some((other) => dot(normal, other) > 1 - 1e-8)) throw new Error("duplicate oriented normals are not permitted");
    normals.push(normal);
    const normalGrowthVelocity = positive(entry.normalGrowthVelocity, `${orientationId} normal velocity`);
    const uncertainty = finite(entry.uncertainty, `${orientationId} uncertainty`);
    if (uncertainty < 0) throw new RangeError(`${orientationId} uncertainty must be nonnegative`);
    if (!(normalGrowthVelocity - 3 * uncertainty > 0)) throw new Error(`${orientationId} velocity is not positive at the three-sigma lower bound`);
    return { orientationId, normal, normalGrowthVelocity, uncertainty };
  });
  const geometry = buildNormalizedKineticWulffGeometry(orientations, intrinsicDimension);
  return { schema: ATTACHMENT_KINETICS_RESPONSE_SCHEMA, requestSha256, structureSha256,
    intrinsicDimension, orientationBasisCartesian, method, drivingCondition,
    units: "metre per second", orientations, validation: { ...validation }, geometry,
    responseAccepted: true, candidateSetChanged: false, candidateRankingChanged: false,
    interfacialFreeEnergyUsed: false, actionBarrierInferred: false,
    attachmentProbabilityInferred: false, physicalTimeIntegrated: false, targetUsed: false };
}

export function evaluateKineticHabitScore({ occupiedPositions, emittedPositions,
  orientationBasisCartesian, orientations, maximumAngleRadians }) {
  const dimension = orientationBasisCartesian?.length;
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsic dimension must be 2 or 3");
  const frame = basis(orientationBasisCartesian, dimension);
  const occupied = (occupiedPositions || []).map((entry, index) => {
    if (!Array.isArray(entry) || entry.length !== 3) throw new TypeError(`occupied position ${index + 1} must have 3 components`);
    return entry.map((value, axis) => finite(value, `occupied position ${index + 1}[${axis}]`));
  });
  const emitted = (emittedPositions || []).map((entry, index) => {
    if (!Array.isArray(entry) || entry.length !== 3) throw new TypeError(`emitted position ${index + 1} must have 3 components`);
    return entry.map((value, axis) => finite(value, `emitted position ${index + 1}[${axis}]`));
  });
  if (occupied.length < dimension + 1 || !emitted.length) return { available: false, supported: false,
    reason: !emitted.length ? "candidate emits no novel sites" : "too few occupied sites to resolve an outward normal",
    score: 0, targetUsed: false };
  const centroid = (points) => points[0].map((_, axis) =>
    points.reduce((sum, point) => sum + point[axis], 0) / points.length);
  const center = centroid(occupied); const freshCenter = centroid(emitted);
  const outward = freshCenter.map((value, axis) => value - center[axis]);
  const intrinsic = cartesianNormalToIntrinsic(outward, frame);
  if (!intrinsic) return { available: true, supported: false,
    reason: "candidate outward direction is unresolved in the intrinsic specimen frame", score: 0, targetUsed: false };
  const mapped = orientations.map((entry) => ({ orientationId: entry.orientationId, normal: entry.normal,
    interfacialFreeEnergy: entry.normalGrowthVelocity, uncertainty: entry.uncertainty }));
  const estimate = orientedEnergyKernelEstimate(mapped, intrinsic, maximumAngleRadians);
  if (!estimate.supported) return { available: true, supported: false, reason: estimate.reason, score: 0,
    candidateNormalCartesian: normalized(outward, "candidate outward normal"),
    candidateNormalIntrinsic: intrinsic, interpolation: estimate, targetUsed: false };
  const normalGrowthVelocity = estimate.interfacialFreeEnergy;
  const { interfacialFreeEnergy: _internalScalar, uncertainty: _internalUncertainty, ...estimateAudit } = estimate;
  const interpolation = { ...estimateAudit, normalGrowthVelocityMetrePerSecond: normalGrowthVelocity,
    velocityUncertaintyMetrePerSecond: estimate.uncertainty,
    interfacialFreeEnergyUsed: false };
  const logReference = orientations.reduce((sum, entry) => sum + Math.log(entry.normalGrowthVelocity), 0)
    / orientations.length;
  const logVelocityContrast = Math.log(normalGrowthVelocity) - logReference;
  return { available: true, supported: true, reason: "validated oriented velocity coverage",
    score: Math.tanh(logVelocityContrast), normalGrowthVelocityMetrePerSecond: normalGrowthVelocity,
    velocityUncertaintyMetrePerSecond: estimate.uncertainty, logVelocityContrast,
    candidateNormalCartesian: normalized(outward, "candidate outward normal"),
    candidateNormalIntrinsic: intrinsic, interpolation,
    candidateSetChanged: false, candidateGeometryChanged: false, hardAdmissionChanged: false,
    actionBarrierInferred: false, attachmentProbabilityInferred: false,
    physicalTimeIntegrated: false, targetUsed: false };
}

export function matchedKineticHabitRankingAudit(records) {
  return { ...matchedWulffRankingAudit(records), auditKind: "orientation-resolved kinetic-habit ranking",
    physicalTimeIntegrated: false, targetUsed: false };
}
