export const INTERFACE_FLUX_REQUEST_SCHEMA = "gcts-spatial-interface-flux-request-v1";
export const INTERFACE_FLUX_RESPONSE_SCHEMA = "gcts-spatial-interface-flux-response-v1";

const EPS = 1e-10;

function text(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function number(value, label) {
  const result = Number(value);
  if (!Number.isFinite(result)) throw new TypeError(`${label} must be finite`);
  return result;
}

function positive(value, label) {
  const result = number(value, label);
  if (!(result > 0)) throw new RangeError(`${label} must be positive`);
  return result;
}

function sha(value, label) {
  const result = text(value, label).toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(result)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return result;
}

function vector(value, label, length = 3) {
  if (!Array.isArray(value) || value.length !== length) throw new TypeError(`${label} must contain ${length} components`);
  return value.map((entry, index) => number(entry, `${label}[${index}]`));
}

function unit(value, label, length = 3) {
  const result = vector(value, label, length); const norm = Math.hypot(...result);
  if (!(norm > EPS)) throw new RangeError(`${label} must be nonzero`);
  return result.map((entry) => entry / norm);
}

function dot(first, second) { return first.reduce((sum, entry, index) => sum + entry * second[index], 0); }

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonical(value[key])]));
  return value;
}

export async function interfaceFluxSha256(value) {
  const bytes = new TextEncoder().encode(typeof value === "string" ? value : JSON.stringify(canonical(value)));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((entry) => entry.toString(16).padStart(2, "0")).join("");
}

export function buildInterfaceFluxRequest(input) {
  if (input?.targetUsed === true || input?.targetCoordinatesEmbedded === true) {
    throw new Error("an interface-flux request cannot use a growth target");
  }
  const structureSha256 = sha(input.structureSha256, "structure SHA-256");
  const interfaceGeometrySha256 = sha(input.interfaceGeometrySha256, "interface geometry SHA-256");
  const species = [...new Set((input.species || []).map((entry) => text(String(entry), "species")))].sort();
  if (!species.length) throw new Error("at least one transported species is required");
  return {
    schema: INTERFACE_FLUX_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId), materialName: text(input.materialName, "material name"),
      species, structureSha256, interfaceGeometrySha256,
      coordinateFrame: "supplied Cartesian specimen coordinates in angstrom",
      interfaceConfiguration: input.interfaceConfiguration || null,
      publicBoundary: input.publicBoundary || null,
      sourceProvenance: input.sourceProvenance || null,
      recordedConditions: input.recordedConditions || null,
    },
    calculation: {
      quantity: "steady spatially resolved net incorporation flux over the declared solid interface",
      suitableMethods: ["steady multicomponent diffusion or diffusion-advection boundary-value solve",
        "phase-field transport solve with a frozen solid interface", "spatially resolved in-situ interface supply measurement"],
      requiredOutputs: ["predeclared interface quadrature positions, outward normals, area weights, and species-resolved incorporation fluxes",
        "one-sigma uncertainties, global steady mass-balance residual, mesh-convergence change, method and boundary-condition digests"],
      fluxUnits: "atoms per square metre per second", responseSchema: INTERFACE_FLUX_RESPONSE_SCHEMA,
    },
    expectedResponse: {
      schema: INTERFACE_FLUX_RESPONSE_SCHEMA, requestSha256: "SHA-256 of this complete request file",
      structureSha256, interfaceGeometrySha256, species,
      patches: [{ patchId: "unique", positionCartesianAngstrom: "array[3]", outwardNormalCartesian: "array[3]",
        areaWeightSquareMetre: "positive", netIncorporationFlux: "positive", uncertainty: "nonnegative",
        speciesFluxes: species.map((speciesId) => ({ species: speciesId, incorporationFlux: "nonnegative" })) }],
    },
    safeguards: {
      requestOnly: true, observationCoordinatesEmbedded: Boolean(input.interfaceConfiguration),
      targetCoordinatesEmbedded: false, targetUsedForSelection: false,
      geometricVisibilityUsedAsPhysicalFlux: false, attachmentVelocityUsedAsFlux: false,
      interfacialEnergyUsedAsFlux: false, fluxMayOnlyRankTheUnchangedExactCandidateSetAfterExplicitOptIn: true,
      diffusionCoefficientInferred: false, attachmentProbabilityInferred: false, physicalTimeIntegrated: false,
    },
  };
}

export function validateInterfaceFluxResponse(response, expected) {
  if (response?.schema !== INTERFACE_FLUX_RESPONSE_SCHEMA) throw new Error("unsupported interface-flux response schema");
  const requestSha256 = sha(response.requestSha256, "response request SHA-256");
  const structureSha256 = sha(response.structureSha256, "response structure SHA-256");
  const interfaceGeometrySha256 = sha(response.interfaceGeometrySha256, "response interface geometry SHA-256");
  if (requestSha256 !== sha(expected.requestSha256, "expected request SHA-256")) throw new Error("response does not match the exact request");
  if (structureSha256 !== sha(expected.structureSha256, "expected structure SHA-256")) throw new Error("response does not match the exact specimen");
  if (interfaceGeometrySha256 !== sha(expected.interfaceGeometrySha256, "expected interface geometry SHA-256")) {
    throw new Error("response does not match the exact frozen interface geometry");
  }
  if (response.fluxUnits !== "atoms per square metre per second") throw new Error("unsupported interface-flux units");
  const species = [...new Set((response.species || []).map((entry) => text(String(entry), "response species")))].sort();
  const expectedSpecies = [...new Set((expected.species || []).map(String))].sort();
  if (JSON.stringify(species) !== JSON.stringify(expectedSpecies)) throw new Error("response species set mismatch");
  const method = { family: text(response.method?.family, "method family"), program: text(response.method?.program, "method program"),
    version: response.method?.version == null ? null : String(response.method.version),
    settingsSha256: sha(response.method?.settingsSha256, "method settings SHA-256"),
    boundaryConditionsSha256: sha(response.method?.boundaryConditionsSha256, "boundary-condition SHA-256") };
  const validation = response.validation || {};
  for (const field of ["passed", "converged", "steadyStateVerified", "uncertaintyReported",
    "interfaceMeshPredeclared", "speciesBalanceChecked"]) if (validation[field] !== true) {
    throw new Error(`validation.${field} must be true`);
  }
  const massBalanceRelativeResidual = Math.abs(number(validation.massBalanceRelativeResidual, "mass-balance residual"));
  const meshConvergenceRelativeChange = Math.abs(number(validation.meshConvergenceRelativeChange, "mesh-convergence change"));
  if (massBalanceRelativeResidual > 1e-3) throw new Error("steady mass-balance residual exceeds 0.1%");
  if (meshConvergenceRelativeChange > .05) throw new Error("mesh-convergence change exceeds 5%");
  if (!Array.isArray(response.patches) || response.patches.length < 4) throw new Error("at least four interface patches are required");
  const ids = new Set();
  const patches = response.patches.map((entry, index) => {
    const patchId = text(entry?.patchId, `patch ${index + 1} ID`);
    if (ids.has(patchId)) throw new Error(`duplicate interface patch ID ${patchId}`); ids.add(patchId);
    const positionCartesianAngstrom = vector(entry.positionCartesianAngstrom, `${patchId} position`);
    const outwardNormalCartesian = unit(entry.outwardNormalCartesian, `${patchId} outward normal`);
    const areaWeightSquareMetre = positive(entry.areaWeightSquareMetre, `${patchId} area weight`);
    const netIncorporationFlux = positive(entry.netIncorporationFlux, `${patchId} net incorporation flux`);
    const uncertainty = number(entry.uncertainty, `${patchId} uncertainty`);
    if (uncertainty < 0 || !(netIncorporationFlux - 3 * uncertainty > 0)) {
      throw new Error(`${patchId} flux must remain positive at its three-sigma lower bound`);
    }
    if (!Array.isArray(entry.speciesFluxes) || entry.speciesFluxes.length !== species.length) {
      throw new Error(`${patchId} must report every transported species exactly once`);
    }
    const seen = new Set(); const speciesFluxes = entry.speciesFluxes.map((record) => {
      const speciesId = text(record?.species, `${patchId} species`);
      if (!species.includes(speciesId) || seen.has(speciesId)) throw new Error(`${patchId} has an invalid species-flux list`);
      seen.add(speciesId); const incorporationFlux = number(record.incorporationFlux, `${patchId} ${speciesId} flux`);
      if (incorporationFlux < 0) throw new Error(`${patchId} species incorporation fluxes must be nonnegative`);
      return { species: speciesId, incorporationFlux };
    }).sort((a, b) => a.species.localeCompare(b.species));
    const sum = speciesFluxes.reduce((total, record) => total + record.incorporationFlux, 0);
    if (Math.abs(sum - netIncorporationFlux) > 1e-6 * Math.max(1, netIncorporationFlux)) {
      throw new Error(`${patchId} species fluxes do not sum to the net incorporation flux`);
    }
    return { patchId, positionCartesianAngstrom, outwardNormalCartesian, areaWeightSquareMetre,
      netIncorporationFlux, uncertainty, speciesFluxes };
  });
  return { schema: INTERFACE_FLUX_RESPONSE_SCHEMA, requestSha256, structureSha256, interfaceGeometrySha256,
    species, fluxUnits: response.fluxUnits, method, validation: { ...validation, massBalanceRelativeResidual,
      meshConvergenceRelativeChange }, patches, responseAccepted: true,
    candidateSetChanged: false, candidateRankingChanged: false, diffusionCoefficientInferred: false,
    attachmentVelocityInferred: false, attachmentProbabilityInferred: false,
    physicalTimeIntegrated: false, targetUsed: false };
}

export function evaluateInterfaceFluxScore({ occupiedPositions, emittedPositions, patches,
  maximumSpatialReachRelativeRadius = .55, maximumAngleRadians = Math.PI / 3 }) {
  const occupied = (occupiedPositions || []).map((entry, index) => vector(entry, `occupied position ${index + 1}`));
  const emitted = (emittedPositions || []).map((entry, index) => vector(entry, `emitted position ${index + 1}`));
  if (occupied.length < 4 || !emitted.length) return { available: false, supported: false,
    reason: !emitted.length ? "candidate emits no novel sites" : "too few occupied sites to resolve the finite interface",
    score: 0, targetUsed: false };
  if (!Array.isArray(patches) || !patches.length) throw new Error("validated interface patches are required");
  const centroid = (points) => points[0].map((_, axis) => points.reduce((sum, point) => sum + point[axis], 0) / points.length);
  const center = centroid(occupied); const freshCenter = centroid(emitted);
  const outward = freshCenter.map((entry, axis) => entry - center[axis]); const candidateNormal = unit(outward, "candidate outward normal");
  const radius = Math.max(EPS, ...occupied.map((position) => Math.hypot(...position.map((entry, axis) => entry - center[axis]))));
  const spatialReach = positive(maximumSpatialReachRelativeRadius, "relative spatial reach") * radius;
  const angularReach = positive(maximumAngleRadians, "angular reach");
  const records = patches.map((patch) => {
    const position = vector(patch.positionCartesianAngstrom, `${patch.patchId} position`);
    const normal = unit(patch.outwardNormalCartesian, `${patch.patchId} normal`);
    const distance = Math.hypot(...position.map((entry, axis) => entry - freshCenter[axis]));
    const angle = Math.acos(Math.max(-1, Math.min(1, dot(candidateNormal, normal))));
    const spatial = Math.max(0, 1 - distance / spatialReach); const angular = Math.max(0, 1 - angle / angularReach);
    return { patch, distance, angle, weight: spatial * spatial * angular * angular };
  }).filter((record) => record.weight > 0);
  if (!records.length) return { available: true, supported: false,
    reason: "candidate lies outside the validated spatial/angular interface-flux reach", score: 0,
    candidateCenterCartesianAngstrom: freshCenter, candidateNormalCartesian: candidateNormal,
    characteristicRadiusAngstrom: radius, targetUsed: false };
  const weightSum = records.reduce((sum, record) => sum + record.weight, 0);
  const logFlux = records.reduce((sum, record) => sum + record.weight * Math.log(record.patch.netIncorporationFlux), 0) / weightSum;
  const uncertainty = Math.sqrt(records.reduce((sum, record) => sum
    + (record.weight * record.patch.uncertainty) ** 2, 0)) / weightSum;
  const reference = patches.reduce((sum, patch) => sum + Math.log(positive(patch.netIncorporationFlux, `${patch.patchId} flux`)), 0)
    / patches.length;
  const logFluxContrast = logFlux - reference;
  return { available: true, supported: true, reason: "validated local interface-flux coverage",
    score: Math.tanh(logFluxContrast), netIncorporationFlux: Math.exp(logFlux), uncertainty,
    logFluxContrast, candidateCenterCartesianAngstrom: freshCenter, candidateNormalCartesian: candidateNormal,
    characteristicRadiusAngstrom: radius, contributingPatchIds: records.map((record) => record.patch.patchId),
    maximumSpatialReachRelativeRadius, maximumAngleRadians,
    candidateSetChanged: false, candidateGeometryChanged: false, hardAdmissionChanged: false,
    diffusionCoefficientInferred: false, attachmentVelocityInferred: false,
    attachmentProbabilityInferred: false, physicalTimeIntegrated: false, targetUsed: false };
}

export function matchedInterfaceFluxRankingAudit(records) {
  const rows = (records || []).map((entry) => ({ candidateId: text(entry.candidateId, "candidate ID"),
    baselineScore: number(entry.baselineScore, "baseline score"), rankedScore: number(entry.rankedScore, "ranked score"),
    supported: entry.supported === true }));
  if (!rows.length) return { candidateCount: 0, supportedCandidates: 0, abstainedCandidates: 0,
    rankInversions: 0, maximumRankInversions: 0, candidateSetIdentical: true,
    baselineLeader: null, rankedLeader: null, leaderChanged: false, targetUsed: false };
  const order = (key) => [...rows].sort((a, b) => b[key] - a[key] || a.candidateId.localeCompare(b.candidateId));
  const baseline = order("baselineScore"); const ranked = order("rankedScore");
  const baselineRank = new Map(baseline.map((entry, index) => [entry.candidateId, index]));
  let rankInversions = 0;
  for (let first = 0; first < ranked.length; first += 1) for (let second = first + 1; second < ranked.length; second += 1) {
    if (baselineRank.get(ranked[first].candidateId) > baselineRank.get(ranked[second].candidateId)) rankInversions += 1;
  }
  const supportedCandidates = rows.filter((entry) => entry.supported).length;
  return { auditKind: "spatial interface-flux ranking", candidateCount: rows.length, supportedCandidates,
    abstainedCandidates: rows.length - supportedCandidates, rankInversions,
    maximumRankInversions: rows.length * (rows.length - 1) / 2, candidateSetIdentical: true,
    baselineLeader: baseline[0].candidateId, rankedLeader: ranked[0].candidateId,
    leaderChanged: baseline[0].candidateId !== ranked[0].candidateId,
    candidateGeometryChanged: false, hardAdmissionChanged: false, targetUsed: false };
}
