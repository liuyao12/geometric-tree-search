export const ACTION_BARRIER_REQUEST_SCHEMA = "gcts-frozen-frontier-action-barrier-request-v1";
export const ACTION_BARRIER_RESPONSE_SCHEMA = "gcts-frozen-frontier-action-barrier-response-v1";

const finite = (value) => Number.isFinite(Number(value));

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function finiteVector(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(finite)) {
    throw new TypeError(`${label} must be a finite Cartesian three-vector`);
  }
  return value.map(Number);
}

function normalizedSite(site, label) {
  return {
    species: requiredText(site?.species, `${label} species`),
    positionAngstrom: finiteVector(site?.positionAngstrom, `${label} position`),
  };
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonicalValue(value[key])]));
  return value;
}

export function canonicalActionBarrierJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export async function actionBarrierSha256(value) {
  const bytes = new TextEncoder().encode(typeof value === "string" ? value : canonicalActionBarrierJson(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function normalizeConfiguration(configuration) {
  if (!configuration || !Array.isArray(configuration.atoms) || !configuration.atoms.length) {
    throw new TypeError("the frozen frontier needs a nonempty initial configuration");
  }
  const cell = configuration.cellVectorsAngstrom == null ? null
    : configuration.cellVectorsAngstrom.map((vector, index) => finiteVector(vector, `cell vector ${index + 1}`));
  if (cell && cell.length !== 3) throw new TypeError("cellVectorsAngstrom must contain three vectors");
  return {
    structureSha256: requiredText(configuration.structureSha256, "initial configuration SHA-256"),
    coordinateUnits: "angstrom",
    atomCount: configuration.atoms.length,
    periodicBoundary: Array.isArray(configuration.periodicBoundary) && configuration.periodicBoundary.length === 3
      ? configuration.periodicBoundary.map(Boolean) : [false, false, false],
    cellVectorsAngstrom: cell,
    atoms: configuration.atoms.map((site, index) => ({
      siteId: String(site.siteId ?? index),
      ...normalizedSite(site, `initial site ${index + 1}`),
    })),
  };
}

function normalizeCandidate(candidate, index) {
  const candidateId = requiredText(candidate?.candidateId, `candidate ${index + 1} id`);
  const emittedSites = Array.isArray(candidate.emittedSites)
    ? candidate.emittedSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} emitted site ${siteIndex + 1}`)) : [];
  const actionSites = Array.isArray(candidate.actionSites)
    ? candidate.actionSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} action site ${siteIndex + 1}`)) : [];
  if (!emittedSites.length || !actionSites.length) {
    throw new Error(`candidate ${candidateId} needs nonempty emittedSites and actionSites`);
  }
  return {
    candidateId,
    candidateDigestSha256: requiredText(candidate.candidateDigestSha256,
      `candidate ${candidateId} digest`),
    actionLabel: requiredText(candidate.actionLabel, `candidate ${candidateId} label`),
    parentType: String(candidate.parentType),
    childType: String(candidate.childType),
    ruleId: String(candidate.ruleId),
    emittedAtomCount: emittedSites.length,
    actionAtomCount: actionSites.length,
    emittedSites,
    actionSites,
    finalStateConstruction: "initial configuration union emittedSites; exact same-species coincidences are shared sites",
  };
}

export async function buildFrozenActionBarrierRequest(input) {
  if (input?.targetUsed === true || input?.candidateSetTargetUsed === true) {
    throw new Error("a frozen action-barrier request cannot use a growth target");
  }
  if (!Array.isArray(input?.candidates) || !input.candidates.length) {
    throw new Error("a frozen action-barrier request needs at least one hard-admitted candidate");
  }
  const initialConfiguration = normalizeConfiguration(input.initialConfiguration);
  const candidates = input.candidates.map(normalizeCandidate)
    .sort((first, second) => first.candidateId.localeCompare(second.candidateId));
  if (new Set(candidates.map((candidate) => candidate.candidateId)).size !== candidates.length) {
    throw new Error("frozen frontier candidate IDs must be unique");
  }
  const candidateBatchSha256 = await actionBarrierSha256(candidates.map((candidate) => ({
    candidateId: candidate.candidateId,
    candidateDigestSha256: candidate.candidateDigestSha256,
    emittedSites: candidate.emittedSites,
    actionSites: candidate.actionSites,
  })));
  return {
    schema: ACTION_BARRIER_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId),
      materialName: String(input.materialName),
      elements: [...new Set((input.elements || []).map(String))].sort(),
      sourceProvenance: input.sourceProvenance || null,
    },
    frontier: {
      candidateBatchSha256,
      candidateCount: candidates.length,
      initialConfiguration,
      candidates,
      candidateSetFrozenBeforeRequest: true,
      candidateGeometryFrozenBeforeRequest: true,
      hardAdmissionFrozenBeforeRequest: true,
    },
    calculation: {
      quantity: "candidate-resolved transition barriers on one exact frozen frontier",
      suitableMethods: ["nudged elastic band", "dimer or saddle search", "validated enhanced-sampling path"],
      requiredOutputs: ["one converged record for every candidate ID", "explicit initial and final geometry digests",
        "at least three energy images", "maximum residual force", "uncertainty and method provenance"],
      units: { coordinates: "angstrom", energy: "electronvolt", force: "electronvolt per angstrom" },
      responseSchema: ACTION_BARRIER_RESPONSE_SCHEMA,
    },
    safeguards: {
      requestOnly: true,
      targetCoordinatesEmbedded: false,
      geometricScoresUsedAsEnergyLabels: false,
      searchStepsUsedAsPhysicalTime: false,
      candidateSetMayChangeAfterResponse: false,
      hardAdmissionMayChangeAfterResponse: false,
      responseScope: "ranking this exact candidate batch only",
    },
  };
}

export async function frozenActionBarrierRequestReceipt(request) {
  if (request?.schema !== ACTION_BARRIER_REQUEST_SCHEMA) throw new Error("invalid action-barrier request schema");
  return {
    requestSha256: await actionBarrierSha256(request),
    candidateBatchSha256: request.frontier.candidateBatchSha256,
    initialStructureSha256: request.frontier.initialConfiguration.structureSha256,
    candidateCount: request.frontier.candidates.length,
  };
}

function median(values) {
  const sorted = [...values].sort((first, second) => first - second);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function robustBarrierScores(records) {
  const barriers = records.map((record) => record.barrierElectronVolt);
  const center = median(barriers);
  const mad = median(barriers.map((value) => Math.abs(value - center)));
  const range = Math.max(...barriers) - Math.min(...barriers);
  const scale = Math.max(1.4826 * mad, range / 4, 1e-9);
  return {
    centerElectronVolt: center,
    scaleElectronVolt: scale,
    records: records.map((record) => ({ ...record,
      lowerBarrierScore: Math.tanh((center - record.barrierElectronVolt) / (2 * scale)) })),
  };
}

export function validateFrozenActionBarrierResponse(response, expected) {
  if (response?.schema !== ACTION_BARRIER_RESPONSE_SCHEMA) {
    throw new Error(`response schema must be ${ACTION_BARRIER_RESPONSE_SCHEMA}`);
  }
  if (!expected || typeof expected !== "object") throw new TypeError("expected request receipt is required");
  if (response.requestSha256 !== expected.requestSha256
      || response.candidateBatchSha256 !== expected.candidateBatchSha256
      || response.initialStructureSha256 !== expected.initialStructureSha256) {
    throw new Error("response is not bound to this exact request, configuration, and candidate batch");
  }
  const method = response.method || {};
  const methodSummary = {
    family: requiredText(method.family, "method family"),
    program: requiredText(method.program, "method program"),
    version: method.version == null ? null : String(method.version),
    settingsSha256: requiredText(method.settingsSha256, "method settings SHA-256"),
  };
  if (!/^[a-f0-9]{64}$/i.test(methodSummary.settingsSha256)) {
    throw new Error("method settings SHA-256 must contain 64 hexadecimal characters");
  }
  const validation = response.validation || {};
  if (!(validation.passed === true && validation.protocolMatchesRequest === true
      && validation.independentHoldout === true && validation.uncertaintyReported === true
      && validation.convergenceReported === true && validation.everyCandidateConverged === true)) {
    throw new Error("action-barrier response has not passed every frozen validation gate");
  }
  if (response.safeguards?.containsGrowthTargetCoordinates !== false
      || response.safeguards?.geometricScoresUsedAsPhysicalLabels !== false
      || response.safeguards?.searchStepsUsedAsPhysicalTime !== false
      || response.safeguards?.candidateSetChanged !== false
      || response.safeguards?.hardAdmissionChanged !== false) {
    throw new Error("action-barrier response safeguards are incomplete or target-tainted");
  }
  if (!Array.isArray(response.records) || response.records.length !== expected.candidates.length) {
    throw new Error(`action-barrier response needs exactly ${expected.candidates.length} candidate records`);
  }
  const expectedById = new Map(expected.candidates.map((candidate) => [candidate.candidateId, candidate]));
  const seen = new Set();
  const records = response.records.map((record, index) => {
    const candidateId = requiredText(record?.candidateId, `barrier record ${index + 1} candidate ID`);
    if (seen.has(candidateId)) throw new Error(`duplicate barrier record for ${candidateId}`);
    seen.add(candidateId);
    const candidate = expectedById.get(candidateId);
    if (!candidate) throw new Error(`unexpected barrier candidate ${candidateId}`);
    if (record.candidateDigestSha256 !== candidate.candidateDigestSha256) {
      throw new Error(`barrier candidate digest mismatch for ${candidateId}`);
    }
    if (!finite(record.barrierElectronVolt) || Number(record.barrierElectronVolt) < 0) {
      throw new TypeError(`barrier for ${candidateId} must be finite and nonnegative`);
    }
    if (!finite(record.maximumForceElectronVoltPerAngstrom)
        || Number(record.maximumForceElectronVoltPerAngstrom) < 0) {
      throw new TypeError(`maximum force for ${candidateId} must be finite and nonnegative`);
    }
    if (!finite(record.uncertaintyElectronVolt) || Number(record.uncertaintyElectronVolt) < 0) {
      throw new TypeError(`uncertainty for ${candidateId} must be finite and nonnegative`);
    }
    if (!Number.isInteger(record.imageCount) || record.imageCount < 3 || record.converged !== true) {
      throw new Error(`barrier path for ${candidateId} is incomplete or unconverged`);
    }
    return {
      candidateId,
      candidateDigestSha256: candidate.candidateDigestSha256,
      barrierElectronVolt: Number(record.barrierElectronVolt),
      uncertaintyElectronVolt: Number(record.uncertaintyElectronVolt),
      maximumForceElectronVoltPerAngstrom: Number(record.maximumForceElectronVoltPerAngstrom),
      imageCount: record.imageCount,
      energyDeltaElectronVolt: finite(record.energyDeltaElectronVolt) ? Number(record.energyDeltaElectronVolt) : null,
      converged: true,
    };
  });
  if ([...expectedById.keys()].some((candidateId) => !seen.has(candidateId))) {
    throw new Error("action-barrier response omitted one or more frozen candidates");
  }
  const normalized = robustBarrierScores(records);
  return {
    schema: 1,
    responseSchema: response.schema,
    requestSha256: response.requestSha256,
    candidateBatchSha256: response.candidateBatchSha256,
    initialStructureSha256: response.initialStructureSha256,
    method: methodSummary,
    validationPassed: true,
    candidateCount: records.length,
    robustNormalization: { centerElectronVolt: normalized.centerElectronVolt,
      scaleElectronVolt: normalized.scaleElectronVolt, transform: "tanh((median(E)-E)/(2*robustScale))" },
    records: normalized.records,
    usedForCandidateGeneration: false,
    usedForHardAdmission: false,
    usedAsPotential: false,
    usedAsPhysicalClock: false,
    targetCoordinatesEmbedded: false,
    eligibleForExactBatchRanking: true,
    eligibleAsTransferableLaw: false,
    physicalInferenceScope: "this initial configuration, candidate batch, method, and validation only",
  };
}
