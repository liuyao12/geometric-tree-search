export const BOLTZMANN_ELECTRON_VOLT_PER_KELVIN = 8.617333262145e-5;
export const FROZEN_KINETIC_MODES = Object.freeze(["rate-maximum", "seeded-kmc"]);

const finite = (value) => Number.isFinite(Number(value));

function requiredUnitUniform(value, label) {
  if (!finite(value) || Number(value) <= 0 || Number(value) >= 1) {
    throw new TypeError(`${label} must be a finite number strictly between zero and one`);
  }
  return Number(value);
}

function logSumExp(values) {
  const maximum = Math.max(...values);
  return maximum + Math.log(values.reduce((sum, value) => sum + Math.exp(value - maximum), 0));
}

function expOrNull(logValue) {
  return logValue > Math.log(Number.MAX_VALUE) || logValue < Math.log(Number.MIN_VALUE)
    ? null : Math.exp(logValue);
}

function normalizedKineticRecord(record, temperatureKelvin) {
  if (typeof record?.candidateId !== "string" || !record.candidateId) {
    throw new TypeError("every kinetic record needs a candidate ID");
  }
  if (!finite(record.barrierElectronVolt) || Number(record.barrierElectronVolt) < 0) {
    throw new TypeError(`barrier for ${record.candidateId} must be finite and nonnegative`);
  }
  if (!finite(record.uncertaintyElectronVolt) || Number(record.uncertaintyElectronVolt) < 0) {
    throw new TypeError(`barrier uncertainty for ${record.candidateId} must be finite and nonnegative`);
  }
  if (!finite(record.attemptFrequencyPerSecond) || Number(record.attemptFrequencyPerSecond) <= 0) {
    throw new TypeError(`attempt frequency for ${record.candidateId} must be finite and positive`);
  }
  if (!finite(record.attemptFrequencyUncertaintyLog10)
      || Number(record.attemptFrequencyUncertaintyLog10) < 0) {
    throw new TypeError(`prefactor uncertainty for ${record.candidateId} must be finite and nonnegative`);
  }
  const barrierElectronVolt = Number(record.barrierElectronVolt);
  const uncertaintyElectronVolt = Number(record.uncertaintyElectronVolt);
  const attemptFrequencyPerSecond = Number(record.attemptFrequencyPerSecond);
  const attemptFrequencyUncertaintyLog10 = Number(record.attemptFrequencyUncertaintyLog10);
  const inverseThermalEnergy = 1
    / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * temperatureKelvin);
  const logRatePerSecond = Math.log(attemptFrequencyPerSecond)
    - barrierElectronVolt * inverseThermalEnergy;
  const log10RatePerSecond = logRatePerSecond / Math.LN10;
  const barrierLog10Uncertainty = uncertaintyElectronVolt * inverseThermalEnergy / Math.LN10;
  return {
    candidateId: record.candidateId,
    candidateDigestSha256: record.candidateDigestSha256 || null,
    barrierElectronVolt,
    uncertaintyElectronVolt,
    attemptFrequencyPerSecond,
    attemptFrequencyUncertaintyLog10,
    logRatePerSecond,
    log10RatePerSecond,
    ratePerSecond: expOrNull(logRatePerSecond),
    log10RateLowerPerSecond: log10RatePerSecond
      - barrierLog10Uncertainty - attemptFrequencyUncertaintyLog10,
    log10RateUpperPerSecond: log10RatePerSecond
      + barrierLog10Uncertainty + attemptFrequencyUncertaintyLog10,
  };
}

export function buildFrozenKineticCompetition(records, {
  temperatureKelvin,
  mode = "rate-maximum",
  eventUniform = .5,
  waitingUniform = .5,
} = {}) {
  if (!Array.isArray(records) || !records.length) {
    throw new TypeError("a kinetic competition needs at least one frozen action record");
  }
  if (!finite(temperatureKelvin) || Number(temperatureKelvin) < 1
      || Number(temperatureKelvin) > 5000) {
    throw new RangeError("temperatureKelvin must be between 1 and 5000 K");
  }
  if (!FROZEN_KINETIC_MODES.includes(mode)) throw new Error(`unsupported kinetic mode ${mode}`);
  const normalizedTemperature = Number(temperatureKelvin);
  const normalized = records.map((record) => normalizedKineticRecord(record, normalizedTemperature))
    .sort((first, second) => first.candidateId.localeCompare(second.candidateId));
  if (new Set(normalized.map((record) => record.candidateId)).size !== normalized.length) {
    throw new Error("kinetic candidate IDs must be unique");
  }
  const logTotalRatePerSecond = logSumExp(normalized.map((record) => record.logRatePerSecond));
  const weighted = normalized.map((record) => ({ ...record,
    probabilityWithinFrozenCatalog: Math.exp(record.logRatePerSecond - logTotalRatePerSecond) }));
  let selected;
  let normalizedEventUniform = null;
  let normalizedWaitingUniform = null;
  if (mode === "rate-maximum") {
    selected = [...weighted].sort((first, second) => second.logRatePerSecond - first.logRatePerSecond
      || first.candidateId.localeCompare(second.candidateId))[0];
  } else {
    normalizedEventUniform = requiredUnitUniform(eventUniform, "eventUniform");
    normalizedWaitingUniform = requiredUnitUniform(waitingUniform, "waitingUniform");
    let cumulative = 0;
    selected = weighted[weighted.length - 1];
    for (const record of weighted) {
      cumulative += record.probabilityWithinFrozenCatalog;
      if (normalizedEventUniform <= cumulative) { selected = record; break; }
    }
  }
  const logWaitingTimeSeconds = mode === "seeded-kmc"
    ? Math.log(-Math.log(normalizedWaitingUniform)) - logTotalRatePerSecond : null;
  const waitingTimeSeconds = logWaitingTimeSeconds == null ? null : expOrNull(logWaitingTimeSeconds);
  return {
    schema: 1,
    model: "catalog-conditional harmonic transition-state competition",
    mode,
    temperatureKelvin: normalizedTemperature,
    candidateCount: weighted.length,
    selectedCandidateId: selected.candidateId,
    selectedLog10RatePerSecond: selected.log10RatePerSecond,
    selectedRatePerSecond: selected.ratePerSecond,
    selectedProbabilityWithinFrozenCatalog: selected.probabilityWithinFrozenCatalog,
    totalRatePerSecond: expOrNull(logTotalRatePerSecond),
    log10TotalRatePerSecond: logTotalRatePerSecond / Math.LN10,
    eventUniform: normalizedEventUniform,
    waitingUniform: normalizedWaitingUniform,
    waitingTimeSeconds,
    log10WaitingTimeSeconds: logWaitingTimeSeconds == null ? null : logWaitingTimeSeconds / Math.LN10,
    records: weighted,
    candidateSetChanged: false,
    hardAdmissionChanged: false,
    targetUsed: false,
    catalogCompleteBeyondFrozenFrontier: false,
    catalogConditionalProbability: true,
    catalogConditionalClock: mode === "seeded-kmc",
    claimBoundary: "Rates and any waiting-time draw are conditional on the enumerated hard-admitted actions in this exact frozen frontier, the supplied barriers and prefactors, and the declared temperature. Missing mechanisms, recrossing, quantum effects, correlated events, and model error are not inferred away.",
  };
}
