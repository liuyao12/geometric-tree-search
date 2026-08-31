export const ACTION_BARRIER_REQUEST_SCHEMA = "gcts-frozen-frontier-action-barrier-request-v2";
export const ACTION_BARRIER_RESPONSE_SCHEMA = "gcts-frozen-frontier-action-barrier-response-v2";

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
  const eventDirection = candidate.eventDirection == null ? "attach"
    : requiredText(candidate.eventDirection, `candidate ${candidateId} event direction`);
  if (!["attach", "detach"].includes(eventDirection)) {
    throw new Error(`candidate ${candidateId} eventDirection must be attach or detach`);
  }
  const emittedSites = Array.isArray(candidate.emittedSites)
    ? candidate.emittedSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} emitted site ${siteIndex + 1}`)) : [];
  const removedSites = Array.isArray(candidate.removedSites)
    ? candidate.removedSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} removed site ${siteIndex + 1}`)) : [];
  const actionSites = Array.isArray(candidate.actionSites)
    ? candidate.actionSites.map((site, siteIndex) => normalizedSite(site,
      `candidate ${index + 1} action site ${siteIndex + 1}`)) : [];
  if (!actionSites.length || (eventDirection === "attach" && (!emittedSites.length || removedSites.length))
      || (eventDirection === "detach" && (!removedSites.length || emittedSites.length))) {
    throw new Error(`candidate ${candidateId} needs one nonempty ${eventDirection === "attach" ? "emittedSites" : "removedSites"} set, the opposite set empty, and nonempty actionSites`);
  }
  return {
    candidateId,
    candidateDigestSha256: requiredText(candidate.candidateDigestSha256,
      `candidate ${candidateId} digest`),
    actionLabel: requiredText(candidate.actionLabel, `candidate ${candidateId} label`),
    eventDirection,
    parentType: String(candidate.parentType),
    childType: String(candidate.childType),
    ruleId: String(candidate.ruleId),
    emittedAtomCount: emittedSites.length,
    removedAtomCount: removedSites.length,
    actionAtomCount: actionSites.length,
    emittedSites,
    removedSites,
    actionSites,
    finalStateConstruction: eventDirection === "attach"
      ? "initial configuration union emittedSites; exact same-species coincidences are shared sites"
      : "initial configuration minus removedSites; retained shared support remains unchanged",
  };
}

function stateSiteKey(site) {
  return `${site.species}\u0000${site.positionAngstrom.map((value) => Number(value).toPrecision(15)).join(",")}`;
}

function sortedStateSites(sites) {
  return sites.map((site) => ({ species: site.species, positionAngstrom: [...site.positionAngstrom] }))
    .sort((first, second) => stateSiteKey(first).localeCompare(stateSiteKey(second)));
}

export async function frozenActionStateGeometrySha256(sites) {
  const normalized = (Array.isArray(sites) ? sites : []).map((site, index) =>
    normalizedSite(site, `state site ${index + 1}`));
  return actionBarrierSha256({ coordinateUnits: "angstrom", atoms: sortedStateSites(normalized) });
}

async function bindCandidateStateGeometry(candidate, initialConfiguration) {
  const initialSites = initialConfiguration.atoms.map(({ species, positionAngstrom }) =>
    ({ species, positionAngstrom }));
  const counts = new Map();
  initialSites.forEach((site) => counts.set(stateSiteKey(site), (counts.get(stateSiteKey(site)) || 0) + 1));
  let finalSites = [...initialSites];
  if (candidate.eventDirection === "attach") {
    candidate.emittedSites.forEach((site) => {
      const key = stateSiteKey(site);
      if (!counts.has(key)) {
        finalSites.push(site);
        counts.set(key, 1);
      }
    });
  } else {
    candidate.removedSites.forEach((site) => {
      const key = stateSiteKey(site);
      const count = counts.get(key) || 0;
      if (!count) throw new Error(`detachment candidate ${candidate.candidateId} removes a site absent from the initial configuration`);
      counts.set(key, count - 1);
      const index = finalSites.findIndex((entry) => stateSiteKey(entry) === key);
      finalSites.splice(index, 1);
    });
  }
  const initialGeometrySha256 = await frozenActionStateGeometrySha256(initialSites);
  const finalGeometrySha256 = await frozenActionStateGeometrySha256(finalSites);
  const canonicalCandidateDigest = await actionBarrierSha256({
    candidateId: candidate.candidateId, eventDirection: candidate.eventDirection,
    emittedSites: candidate.emittedSites, removedSites: candidate.removedSites,
    actionSites: candidate.actionSites,
  });
  if (candidate.candidateDigestSha256 !== canonicalCandidateDigest) {
    throw new Error(`candidate ${candidate.candidateId} digest does not match its exact direction and geometry`);
  }
  return { ...candidate, initialGeometrySha256, finalGeometrySha256,
    initialAtomCount: initialSites.length, finalAtomCount: finalSites.length };
}

export async function buildFrozenActionBarrierRequest(input) {
  if (input?.targetUsed === true || input?.candidateSetTargetUsed === true) {
    throw new Error("a frozen action-barrier request cannot use a growth target");
  }
  if (!Array.isArray(input?.candidates) || !input.candidates.length) {
    throw new Error("a frozen action-barrier request needs at least one hard-admitted candidate");
  }
  const initialConfiguration = normalizeConfiguration(input.initialConfiguration);
  const normalizedCandidates = input.candidates.map(normalizeCandidate);
  const candidates = (await Promise.all(normalizedCandidates.map((candidate) =>
    bindCandidateStateGeometry(candidate, initialConfiguration))))
    .sort((first, second) => first.candidateId.localeCompare(second.candidateId));
  if (new Set(candidates.map((candidate) => candidate.candidateId)).size !== candidates.length) {
    throw new Error("frozen frontier candidate IDs must be unique");
  }
  const candidateBatchSha256 = await actionBarrierSha256(candidates.map((candidate) => ({
    candidateId: candidate.candidateId,
    candidateDigestSha256: candidate.candidateDigestSha256,
    eventDirection: candidate.eventDirection,
    emittedSites: candidate.emittedSites,
    removedSites: candidate.removedSites,
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
      quantity: "candidate-resolved attachment and/or exact leaf-detachment transition barriers on one frozen frontier",
      suitableMethods: ["nudged elastic band", "dimer or saddle search", "validated enhanced-sampling path"],
      requiredOutputs: ["one converged record for every candidate ID", "the supplied exact initial and final geometry digests",
        "at least three energy images", "maximum residual force", "barrier uncertainty and method provenance"],
      optionalMicroscopicInverseOutputs: ["energyDeltaElectronVolt between the exact final and initial states",
        "energyDeltaUncertaintyElectronVolt from the same method-specific calculation"],
      optionalKineticOutputs: ["one positive converged attemptFrequencyPerSecond for every candidate ID",
        "attemptFrequencyUncertaintyLog10", "prefactor method and settings SHA-256",
        "explicit requested-frontier-only catalog scope and recrossing declaration"],
      optionalKineticResponseContract: {
        rootKinetics: { model: "harmonic-transition-state-theory", prefactorMethod: "method name",
          prefactorSettingsSha256: "64 hexadecimal characters",
          recrossingCorrection: "included | not-included",
          catalogScope: "requested-hard-admitted-actions-only" },
        validationFlags: ["prefactorsReported", "everyPrefactorConverged",
          "prefactorUncertaintyReported"],
        everyCandidateRecord: { attemptFrequencyPerSecond: "finite positive s^-1",
          attemptFrequencyUncertaintyLog10: "finite nonnegative decades",
          prefactorConverged: true },
      },
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
      reversibleGeometryDoesNotImplyDetailedBalance: true,
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
  const kinetics = response.kinetics == null ? null : {
    model: requiredText(response.kinetics.model, "kinetic prefactor model"),
    prefactorMethod: requiredText(response.kinetics.prefactorMethod, "prefactor method"),
    prefactorSettingsSha256: requiredText(response.kinetics.prefactorSettingsSha256,
      "prefactor settings SHA-256"),
    recrossingCorrection: requiredText(response.kinetics.recrossingCorrection,
      "recrossing correction declaration"),
    catalogScope: requiredText(response.kinetics.catalogScope, "kinetic catalog scope"),
  };
  if (kinetics) {
    if (kinetics.model !== "harmonic-transition-state-theory") {
      throw new Error("kinetic model must be harmonic-transition-state-theory");
    }
    if (!/^[a-f0-9]{64}$/i.test(kinetics.prefactorSettingsSha256)) {
      throw new Error("prefactor settings SHA-256 must contain 64 hexadecimal characters");
    }
    if (!["included", "not-included"].includes(kinetics.recrossingCorrection)) {
      throw new Error("recrossingCorrection must be included or not-included");
    }
    if (kinetics.catalogScope !== "requested-hard-admitted-actions-only") {
      throw new Error("kinetic catalog scope must remain the requested hard-admitted actions only");
    }
    if (!(validation.prefactorsReported === true && validation.everyPrefactorConverged === true
        && validation.prefactorUncertaintyReported === true)) {
      throw new Error("kinetic prefactors have not passed every frozen validation gate");
    }
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
  if (!kinetics && response.records.some((record) => record?.attemptFrequencyPerSecond != null
      || record?.attemptFrequencyUncertaintyLog10 != null || record?.prefactorConverged != null)) {
    throw new Error("per-candidate kinetic fields require the complete response kinetics declaration");
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
    if (record.initialGeometrySha256 !== candidate.initialGeometrySha256
        || record.finalGeometrySha256 !== candidate.finalGeometrySha256) {
      throw new Error(`barrier path geometry digest mismatch for ${candidateId}`);
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
    if ((record.energyDeltaElectronVolt != null && !finite(record.energyDeltaElectronVolt))
        || (record.energyDeltaUncertaintyElectronVolt != null
          && !finite(record.energyDeltaUncertaintyElectronVolt))) {
      throw new TypeError(`energy delta fields for ${candidateId} must be finite when supplied`);
    }
    const energyDeltaElectronVolt = record.energyDeltaElectronVolt == null
      ? null : Number(record.energyDeltaElectronVolt);
    const energyDeltaUncertaintyElectronVolt = record.energyDeltaUncertaintyElectronVolt == null
      ? null : Number(record.energyDeltaUncertaintyElectronVolt);
    if ((energyDeltaElectronVolt == null) !== (energyDeltaUncertaintyElectronVolt == null)
        || (energyDeltaUncertaintyElectronVolt != null && energyDeltaUncertaintyElectronVolt < 0)) {
      throw new Error(`energy delta and its nonnegative uncertainty must be supplied together for ${candidateId}`);
    }
    if (kinetics && (!finite(record.attemptFrequencyPerSecond)
        || Number(record.attemptFrequencyPerSecond) <= 0
        || !finite(record.attemptFrequencyUncertaintyLog10)
        || Number(record.attemptFrequencyUncertaintyLog10) < 0
        || record.prefactorConverged !== true)) {
      throw new Error(`kinetic prefactor for ${candidateId} is incomplete, invalid, or unconverged`);
    }
    return {
      candidateId,
      candidateDigestSha256: candidate.candidateDigestSha256,
      eventDirection: candidate.eventDirection,
      initialGeometrySha256: candidate.initialGeometrySha256,
      finalGeometrySha256: candidate.finalGeometrySha256,
      barrierElectronVolt: Number(record.barrierElectronVolt),
      uncertaintyElectronVolt: Number(record.uncertaintyElectronVolt),
      maximumForceElectronVoltPerAngstrom: Number(record.maximumForceElectronVoltPerAngstrom),
      imageCount: record.imageCount,
      energyDeltaElectronVolt,
      energyDeltaUncertaintyElectronVolt,
      attemptFrequencyPerSecond: kinetics ? Number(record.attemptFrequencyPerSecond) : null,
      attemptFrequencyUncertaintyLog10: kinetics
        ? Number(record.attemptFrequencyUncertaintyLog10) : null,
      prefactorConverged: Boolean(kinetics),
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
    kinetics,
    kineticsEligible: Boolean(kinetics),
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
    eventDirections: [...new Set(normalized.records.map((record) => record.eventDirection))].sort(),
    reversibleEventGeometryPresent: normalized.records.some((record) => record.eventDirection === "attach")
      && normalized.records.some((record) => record.eventDirection === "detach"),
    thermodynamicReversibilityCertified: false,
    detailedBalanceCertified: false,
  };
}
