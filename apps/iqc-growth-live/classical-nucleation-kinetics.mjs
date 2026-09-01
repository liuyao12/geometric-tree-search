export const CLASSICAL_NUCLEATION_KINETICS_REQUEST_SCHEMA =
  "gcts-classical-nucleation-kinetics-request-v1";
export const CLASSICAL_NUCLEATION_KINETICS_RESPONSE_SCHEMA =
  "gcts-classical-nucleation-kinetics-response-v1";

const BOLTZMANN_JOULE_PER_KELVIN = 1.380649e-23;
const ELECTRON_VOLT_JOULE = 1.602176634e-19;
const LN10 = Math.log(10);

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

function nonnegative(value, label) {
  const number = finite(value, label);
  if (number < 0) throw new RangeError(`${label} must be nonnegative`);
  return number;
}

function digest(value, label) {
  const text = requiredText(value, label).toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(text)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return text;
}

function densityUnits(dimension) {
  return dimension === 3 ? "nucleation sites per cubic metre" : "nucleation sites per square metre";
}

function requireConditionalWork(work) {
  if (!work?.conditionalClassicalModel || work?.targetUsed) {
    throw new Error("accepted target-blind conditional classical nucleation work is required");
  }
  const dimension = Number(work.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("intrinsicDimension must be 2 or 3");
  positive(work.temperatureKelvin, "work temperature");
  positive(work.barrierJoule, "conditional barrier");
  return dimension;
}

export function buildClassicalNucleationKineticsRequest(input) {
  if (input?.targetUsed || input?.targetCoordinatesEmbedded) {
    throw new Error("a nucleation-kinetics request cannot use a growth target");
  }
  const work = input?.nucleationWork;
  const dimension = requireConditionalWork(work);
  const structureSha256 = digest(work.structureSha256, "structure SHA-256");
  const workSha256 = digest(input.workSha256, "nucleation-work SHA-256");
  const interfacialEnergyResponseSha256 = digest(work.interfacialEnergyResponseSha256,
    "interfacial-energy response SHA-256");
  const bulkDrivingForceRequestSha256 = digest(work.bulkDrivingForceRequestSha256,
    "bulk-driving-force request SHA-256");
  const temperatureKelvin = positive(work.temperatureKelvin, "temperature");
  return {
    schema: CLASSICAL_NUCLEATION_KINETICS_REQUEST_SCHEMA,
    generatedAt: String(input.generatedAt),
    application: { name: "Materials Growth Lab", buildId: String(input.buildId) },
    specimen: {
      scenarioId: String(input.scenarioId),
      materialName: requiredText(input.materialName, "material name"),
      structureSha256,
      intrinsicDimension: dimension,
      sourceProvenance: input.sourceProvenance || null,
    },
    coupledClassicalWork: {
      workSha256,
      interfacialEnergyResponseSha256,
      bulkDrivingForceRequestSha256,
      parentPhase: requiredText(work.parentPhase, "parent phase"),
      nucleusPhase: requiredText(work.nucleusPhase, "nucleus phase"),
      temperatureKelvin,
      conditionalBarrierJoule: positive(work.barrierJoule, "conditional barrier"),
      conditionalBarrierUncertaintyJoule: nonnegative(
        Number(work.barrierUncertaintyElectronVolt) * ELECTRON_VOLT_JOULE,
        "conditional barrier uncertainty"),
      criticalScaleMetre: positive(work.criticalScaleMetre, "critical scale"),
    },
    calculation: {
      quantity: "conditional steady-state homogeneous classical nucleation rate density",
      definition: "J = rho_site * Z * f_plus * exp[-DeltaG_star/(k_B T)]",
      rateDensityUnits: dimension === 3 ? "events per cubic metre per second"
        : "events per square metre per second",
      siteDensityUnits: densityUnits(dimension),
      suitableMethods: [
        "critical-nucleus fluctuation or committor analysis with attachment kinetics",
        "mean-first-passage, forward-flux, or calibrated rare-event calculation",
        "experimentally calibrated kinetic prefactor resolved at the declared state",
      ],
      requiredOutputs: [
        "nucleation-site density, Zeldovich factor, and critical-nucleus attachment frequency",
        "one-sigma uncertainty for every kinetic factor",
        "reaction coordinate, ensemble, method, settings digest, convergence and validation declarations",
      ],
      responseSchema: CLASSICAL_NUCLEATION_KINETICS_RESPONSE_SCHEMA,
    },
    expectedResponse: {
      schema: CLASSICAL_NUCLEATION_KINETICS_RESPONSE_SCHEMA,
      requestSha256: "SHA-256 of this complete request file",
      workSha256,
      structureSha256,
      intrinsicDimension: dimension,
      temperatureKelvin,
      phases: { parent: work.parentPhase, nucleus: work.nucleusPhase },
      siteDensity: "finite positive value",
      siteDensityUnits: densityUnits(dimension),
      siteDensityUncertainty: "finite nonnegative one-sigma uncertainty",
      zeldovichFactor: "finite value in (0,1]",
      zeldovichFactorUncertainty: "finite nonnegative one-sigma uncertainty",
      attachmentFrequencyPerSecond: "finite positive critical-nucleus attachment frequency",
      attachmentFrequencyUncertaintyPerSecond: "finite nonnegative one-sigma uncertainty",
      reactionCoordinate: { name: "required", criticalValue: "required finite value",
        definition: "required" },
      method: { family: "required", program: "required", version: "declared or null",
        settingsSha256: "64 hexadecimal characters" },
      validation: { passed: true, converged: true, uncertaintiesReported: true,
        reactionCoordinateValidated: true, steadyStateAssumptionDeclared: true,
        homogeneousNucleationDeclared: true },
    },
    safeguards: {
      requestOnly: true,
      targetCoordinatesEmbedded: false,
      targetUsedForSelection: false,
      barrierAloneCannotProduceARate: true,
      kineticFactorsNotInferredFromGeometry: true,
      responseMayOnlyProduceAConditionalRateDensity: true,
      responseMayNotAlterCandidatesGeometryOrAdmission: true,
      nonclassicalAndHeterogeneousPathwaysRemainOpen: true,
    },
  };
}

export function validateClassicalNucleationKineticsResponse(response, expected) {
  if (response?.schema !== CLASSICAL_NUCLEATION_KINETICS_RESPONSE_SCHEMA) {
    throw new Error("unsupported classical nucleation-kinetics response schema");
  }
  const requestSha256 = digest(response.requestSha256, "request SHA-256");
  const workSha256 = digest(response.workSha256, "work SHA-256");
  const structureSha256 = digest(response.structureSha256, "structure SHA-256");
  if (requestSha256 !== digest(expected.requestSha256, "expected request SHA-256")
      || workSha256 !== digest(expected.workSha256, "expected work SHA-256")
      || structureSha256 !== digest(expected.structureSha256, "expected structure SHA-256")) {
    throw new Error("nucleation-kinetics response is not bound to the frozen request and work");
  }
  const dimension = Number(response.intrinsicDimension);
  if (dimension !== Number(expected.intrinsicDimension) || ![2, 3].includes(dimension)) {
    throw new Error("nucleation-kinetics intrinsic dimension mismatch");
  }
  const temperatureKelvin = positive(response.temperatureKelvin, "temperature");
  if (Math.abs(temperatureKelvin - positive(expected.temperatureKelvin,
    "expected temperature")) > 1e-6) throw new Error("nucleation-kinetics temperature mismatch");
  const parentPhase = requiredText(response.phases?.parent, "parent phase");
  const nucleusPhase = requiredText(response.phases?.nucleus, "nucleus phase");
  if (parentPhase !== requiredText(expected.parentPhase, "expected parent phase")
      || nucleusPhase !== requiredText(expected.nucleusPhase, "expected nucleus phase")) {
    throw new Error("nucleation-kinetics phase identity mismatch");
  }
  const units = densityUnits(dimension);
  if (response.siteDensityUnits !== units) throw new Error(`siteDensityUnits must be '${units}'`);
  const siteDensity = positive(response.siteDensity, "site density");
  const siteDensityUncertainty = nonnegative(response.siteDensityUncertainty,
    "site-density uncertainty");
  const zeldovichFactor = positive(response.zeldovichFactor, "Zeldovich factor");
  if (zeldovichFactor > 1) throw new RangeError("Zeldovich factor must not exceed one");
  const zeldovichFactorUncertainty = nonnegative(response.zeldovichFactorUncertainty,
    "Zeldovich-factor uncertainty");
  const attachmentFrequencyPerSecond = positive(response.attachmentFrequencyPerSecond,
    "attachment frequency");
  const attachmentFrequencyUncertaintyPerSecond = nonnegative(
    response.attachmentFrequencyUncertaintyPerSecond, "attachment-frequency uncertainty");
  if (!(siteDensity - 3 * siteDensityUncertainty > 0)
      || !(zeldovichFactor - 3 * zeldovichFactorUncertainty > 0)
      || zeldovichFactor + 3 * zeldovichFactorUncertainty > 1 + 1e-12
      || !(attachmentFrequencyPerSecond - 3 * attachmentFrequencyUncertaintyPerSecond > 0)) {
    throw new Error("every kinetic factor must remain physically admissible at three sigma");
  }
  const reactionCoordinate = {
    name: requiredText(response.reactionCoordinate?.name, "reaction-coordinate name"),
    criticalValue: finite(response.reactionCoordinate?.criticalValue,
      "reaction-coordinate critical value"),
    definition: requiredText(response.reactionCoordinate?.definition,
      "reaction-coordinate definition"),
  };
  const method = {
    family: requiredText(response.method?.family, "method family"),
    program: requiredText(response.method?.program, "method program"),
    version: response.method?.version == null ? null : String(response.method.version),
    settingsSha256: digest(response.method?.settingsSha256, "method settings SHA-256"),
  };
  for (const field of ["passed", "converged", "uncertaintiesReported",
    "reactionCoordinateValidated", "steadyStateAssumptionDeclared",
    "homogeneousNucleationDeclared"]) {
    if (response.validation?.[field] !== true) throw new Error(`validation.${field} must be true`);
  }
  return {
    schema: CLASSICAL_NUCLEATION_KINETICS_RESPONSE_SCHEMA,
    requestSha256, workSha256, structureSha256, intrinsicDimension: dimension,
    temperatureKelvin, phases: { parent: parentPhase, nucleus: nucleusPhase },
    siteDensity, siteDensityUnits: units, siteDensityUncertainty,
    zeldovichFactor, zeldovichFactorUncertainty,
    attachmentFrequencyPerSecond, attachmentFrequencyUncertaintyPerSecond,
    reactionCoordinate, method, validation: { ...response.validation },
    responseAccepted: true, targetUsed: false,
  };
}

export function buildConditionalClassicalNucleationRate(work, kinetics) {
  const dimension = requireConditionalWork(work);
  if (!kinetics?.responseAccepted || kinetics?.targetUsed) {
    throw new Error("accepted target-blind nucleation-kinetics evidence is required");
  }
  if (kinetics.structureSha256 !== work.structureSha256
      || kinetics.workSha256 == null
      || kinetics.intrinsicDimension !== dimension
      || Math.abs(kinetics.temperatureKelvin - work.temperatureKelvin) > 1e-6
      || kinetics.phases.parent !== work.parentPhase
      || kinetics.phases.nucleus !== work.nucleusPhase) {
    throw new Error("kinetics and conditional work are not bound to the same physical state");
  }
  const thermalEnergyJoule = BOLTZMANN_JOULE_PER_KELVIN * work.temperatureKelvin;
  const barrierThermalUnits = work.barrierJoule / thermalEnergyJoule;
  const logRateDensityPerSi = Math.log(kinetics.siteDensity)
    + Math.log(kinetics.zeldovichFactor)
    + Math.log(kinetics.attachmentFrequencyPerSecond) - barrierThermalUnits;
  const barrierUncertaintyJoule = nonnegative(
    Number(work.barrierUncertaintyElectronVolt) * ELECTRON_VOLT_JOULE,
    "barrier uncertainty");
  const logRateDensitySigma = Math.hypot(
    kinetics.siteDensityUncertainty / kinetics.siteDensity,
    kinetics.zeldovichFactorUncertainty / kinetics.zeldovichFactor,
    kinetics.attachmentFrequencyUncertaintyPerSecond
      / kinetics.attachmentFrequencyPerSecond,
    barrierUncertaintyJoule / thermalEnergyJoule);
  return {
    schema: "gcts-conditional-classical-nucleation-rate-v1",
    intrinsicDimension: dimension,
    structureSha256: work.structureSha256,
    workSha256: kinetics.workSha256,
    kineticsRequestSha256: kinetics.requestSha256,
    parentPhase: work.parentPhase,
    nucleusPhase: work.nucleusPhase,
    temperatureKelvin: work.temperatureKelvin,
    barrierJoule: work.barrierJoule,
    barrierThermalUnits,
    siteDensity: kinetics.siteDensity,
    siteDensityUnits: kinetics.siteDensityUnits,
    zeldovichFactor: kinetics.zeldovichFactor,
    attachmentFrequencyPerSecond: kinetics.attachmentFrequencyPerSecond,
    logRateDensityPerSi,
    log10RateDensityPerSi: logRateDensityPerSi / LN10,
    logRateDensitySigma,
    log10RateDensitySigma: logRateDensitySigma / LN10,
    rateDensityUnits: dimension === 3 ? "events per cubic metre per second"
      : "events per square metre per second",
    uncertaintyModel: "independent one-sigma propagation in log rate from supplied kinetic factors and conditional barrier",
    conditionalSteadyStateHomogeneousCnt: true,
    poissonObservationAssumptionRequired: true,
    candidateSetChanged: false,
    candidateGeometryChanged: false,
    growthRankingChanged: false,
    targetUsed: false,
    claimBoundary: "Conditional steady-state homogeneous classical nucleation rate density from one validated capillarity barrier and independently supplied site density, Zeldovich factor, and critical-nucleus attachment frequency. The rate is not a measured event count, a nonclassical or heterogeneous pathway, a time-dependent depletion model, a complete mechanism, a branch probability, or a growth clock.",
  };
}

export function evaluatePoissonNucleationWindow(rate, characteristicLengthMetre, exposureSeconds) {
  if (!rate?.conditionalSteadyStateHomogeneousCnt || rate?.targetUsed) {
    throw new Error("accepted target-blind conditional nucleation-rate evidence is required");
  }
  const length = positive(characteristicLengthMetre, "observation length");
  const exposure = positive(exposureSeconds, "exposure time");
  const dimension = Number(rate.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("rate dimension must be 2 or 3");
  const observationMeasureSi = length ** dimension;
  const logExpectedEventCount = rate.logRateDensityPerSi
    + Math.log(observationMeasureSi) + Math.log(exposure);
  const log10ExpectedEventCount = logExpectedEventCount / LN10;
  const expectedEventCount = logExpectedEventCount > 700 ? Infinity
    : logExpectedEventCount < -745 ? 0 : Math.exp(logExpectedEventCount);
  const atLeastOneEventProbability = expectedEventCount === Infinity ? 1
    : -Math.expm1(-expectedEventCount);
  const logMedianFirstEventSeconds = Math.log(Math.log(2))
    - rate.logRateDensityPerSi - Math.log(observationMeasureSi);
  return {
    schema: "gcts-conditional-poisson-nucleation-window-v1",
    intrinsicDimension: dimension,
    characteristicLengthMetre: length,
    observationMeasureSi,
    exposureSeconds: exposure,
    logExpectedEventCount,
    log10ExpectedEventCount,
    expectedEventCount,
    atLeastOneEventProbability,
    logMedianFirstEventSeconds,
    log10MedianFirstEventSeconds: logMedianFirstEventSeconds / LN10,
    homogeneousStationaryPoissonAssumption: true,
    finiteObservationOnly: true,
    physicalClockIntegrated: false,
    targetUsed: false,
    claimBoundary: "A Poisson observation-window projection conditional on a constant homogeneous rate density, fixed observation measure, and fixed exposure. It is not an observed induction time, a depletion or impingement model, a finite-site process, spatial correlation, incubation transient, or a clock attached to GCTS actions.",
  };
}
