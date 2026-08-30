import { EXTERNAL_PHYSICS_REQUEST_TEMPLATES, EXTERNAL_PHYSICS_RESPONSE_SCHEMA }
  from "./external-physics-request.mjs";

const finite = (value) => Number.isFinite(Number(value));

function finiteVector(value, label) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(finite)) {
    throw new TypeError(`${label} must be a finite Cartesian three-vector`);
  }
  return value.map(Number);
}

function positive(value, label, allowZero = false) {
  if (!finite(value) || (allowZero ? Number(value) < 0 : Number(value) <= 0)) {
    throw new TypeError(`${label} must be ${allowZero ? "nonnegative" : "positive"}`);
  }
  return Number(value);
}

function text(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function validateTrajectory(results, expectedSites) {
  if (!Array.isArray(results.frames) || results.frames.length < 2) {
    throw new Error("trajectory response needs at least two ordered frames");
  }
  let previousTime = -Infinity;
  const frames = results.frames.map((frame, index) => {
    const timeSeconds = positive(frame.timeSeconds, `trajectory frame ${index + 1} time`, true);
    if (timeSeconds <= previousTime) throw new Error("trajectory frame times must increase strictly");
    previousTime = timeSeconds;
    if (!Array.isArray(frame.positionsAngstrom) || frame.positionsAngstrom.length !== expectedSites) {
      throw new Error(`trajectory frame ${index + 1} must contain ${expectedSites} positions`);
    }
    return { timeSeconds, positionsAngstrom: frame.positionsAngstrom.map((position, site) =>
      finiteVector(position, `trajectory frame ${index + 1} site ${site + 1}`)) };
  });
  return { frameCount: frames.length, timeSpanSeconds: frames.at(-1).timeSeconds - frames[0].timeSeconds,
    siteCoverage: 1 };
}

function validateClock(results) {
  const exposureSeconds = positive(results.exposureSeconds, "clock exposure");
  const eventCount = positive(results.eventCount, "clock event count", true);
  const censoredEventCount = positive(results.censoredEventCount ?? 0, "clock censored count", true);
  const ratePerSecond = positive(results.ratePerSecond, "clock rate", true);
  return { exposureSeconds, eventCount, censoredEventCount, ratePerSecond };
}

function validateBarrier(results) {
  if (!Array.isArray(results.energyProfileElectronVolt) || results.energyProfileElectronVolt.length < 3
      || !results.energyProfileElectronVolt.every(finite)) {
    throw new Error("barrier response needs at least three finite energy-profile images");
  }
  text(results.initialState, "barrier initial state");
  text(results.finalState, "barrier final state");
  const maximumForceElectronVoltPerAngstrom = positive(
    results.maximumForceElectronVoltPerAngstrom, "barrier maximum force", true);
  const energies = results.energyProfileElectronVolt.map(Number);
  return { imageCount: energies.length,
    barrierElectronVolt: Math.max(...energies) - energies[0], maximumForceElectronVoltPerAngstrom };
}

function validateFreeEnergy(results) {
  if (!finite(results.deltaFreeEnergyElectronVolt)) throw new TypeError("free-energy difference must be finite");
  const uncertaintyElectronVolt = positive(results.uncertaintyElectronVolt, "free-energy uncertainty", true);
  const temperatureKelvin = positive(results.temperatureKelvin, "free-energy temperature");
  return { deltaFreeEnergyElectronVolt: Number(results.deltaFreeEnergyElectronVolt),
    uncertaintyElectronVolt, temperatureKelvin, ensemble: text(results.ensemble, "free-energy ensemble") };
}

function validateProbability(results) {
  const transitionCount = positive(results.transitionCount, "transition count", true);
  const exposureSeconds = positive(results.exposureSeconds, "transition exposure");
  const ratePerSecond = positive(results.ratePerSecond, "transition rate", true);
  const independentTrajectoryCount = positive(results.independentTrajectoryCount,
    "independent trajectory count");
  return { transitionCount, exposureSeconds, ratePerSecond, independentTrajectoryCount };
}

function validateForces(results, expectedSites) {
  if (!Array.isArray(results.forceVectorsElectronVoltPerAngstrom)
      || results.forceVectorsElectronVoltPerAngstrom.length !== expectedSites) {
    throw new Error(`force response needs ${expectedSites} site-resolved vectors`);
  }
  results.forceVectorsElectronVoltPerAngstrom.forEach((vector, index) =>
    finiteVector(vector, `force site ${index + 1}`));
  if (!finite(results.totalEnergyElectronVolt)) throw new TypeError("force response total energy must be finite");
  if (results.stressTensorGigaPascal !== undefined && results.stressTensorGigaPascal !== null) {
    if (!Array.isArray(results.stressTensorGigaPascal) || results.stressTensorGigaPascal.length !== 3) {
      throw new TypeError("stress tensor must contain three rows");
    }
    results.stressTensorGigaPascal.forEach((row, index) =>
      finiteVector(row, `stress tensor row ${index + 1}`));
  }
  return { vectorCount: expectedSites, siteCoverage: 1,
    totalEnergyElectronVolt: Number(results.totalEnergyElectronVolt),
    stressAvailable: Array.isArray(results.stressTensorGigaPascal) };
}

const VALIDATORS = Object.freeze({
  trajectory: validateTrajectory,
  clock: validateClock,
  barrier: validateBarrier,
  "free-energy": validateFreeEnergy,
  probability: validateProbability,
  forces: validateForces,
});

export function validateExternalPhysicsResponse(response, expected) {
  if (!response || response.schema !== EXTERNAL_PHYSICS_RESPONSE_SCHEMA) {
    throw new Error(`response schema must be ${EXTERNAL_PHYSICS_RESPONSE_SCHEMA}`);
  }
  if (!expected || typeof expected !== "object") throw new TypeError("expected request receipt is required");
  if (response.requestSha256 !== expected.requestSha256) throw new Error("response request SHA-256 does not match");
  if (response.quantityId !== expected.quantityId || !EXTERNAL_PHYSICS_REQUEST_TEMPLATES[response.quantityId]) {
    throw new Error("response quantity does not match the exported request");
  }
  const role = response.configuration?.role;
  if (!["observation", "growthSeed"].includes(role)) throw new Error("response configuration role is invalid");
  const configuration = expected.configurations?.[role];
  if (!configuration || response.configuration.structureSha256 !== configuration.structureSha256) {
    throw new Error("response configuration SHA-256 does not match the exported structure");
  }
  const method = response.method || {};
  const methodSummary = {
    family: text(method.family, "method family"),
    program: text(method.program, "method program or instrument"),
    version: method.version === null || method.version === undefined ? null : String(method.version),
    settingsSha256: text(method.settingsSha256, "method settings SHA-256"),
  };
  if (!/^[a-f0-9]{64}$/i.test(methodSummary.settingsSha256)) {
    throw new Error("method settings SHA-256 must contain 64 hexadecimal characters");
  }
  const validation = response.validation || {};
  const validationPassed = validation.passed === true && validation.protocolMatchesRequest === true
    && validation.independentHoldout === true && validation.uncertaintyReported === true
    && validation.convergenceReported === true;
  if (!validationPassed) throw new Error("response has not passed every frozen validation gate");
  if (response.safeguards?.containsGrowthTargetCoordinates !== false
      || response.safeguards?.geometricScoresUsedAsPhysicalLabels !== false
      || response.safeguards?.searchStepsUsedAsPhysicalTime !== false) {
    throw new Error("response safeguards are incomplete or target-tainted");
  }
  const quantitySummary = VALIDATORS[response.quantityId](response.results || {}, configuration.atomCount);
  return {
    schema: 1, responseSchema: response.schema, quantityId: response.quantityId,
    configurationRole: role, configurationSha256: configuration.structureSha256,
    requestSha256: response.requestSha256, method: methodSummary, quantitySummary,
    validationPassed: true, eligibleAsSpecimenSpecificEvidence: true,
    eligibleAsTransferableLaw: false, usedForCandidateGeneration: false,
    usedForCandidateRanking: false, usedAsPotential: false, usedAsPhysicalClock: false,
    targetCoordinatesEmbedded: false, physicalInferenceScope: "this configuration, method, and validation only",
  };
}
