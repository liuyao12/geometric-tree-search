const SHA256 = /^[a-f0-9]{64}$/i;
const BOLTZMANN_ELECTRON_VOLT_PER_KELVIN = 8.617333262145e-5;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function requiredSha(value, label) {
  const normalized = requiredText(value, label);
  if (!SHA256.test(normalized)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return normalized.toLowerCase();
}

function optionalSha(value, label) {
  return value == null ? null : requiredSha(value, label);
}

function optionalFinite(value, label, { nonnegative = false, positive = false } = {}) {
  if (value == null) return null;
  if (!Number.isFinite(Number(value))) throw new TypeError(`${label} must be finite`);
  const normalized = Number(value);
  if (positive && normalized <= 0) throw new RangeError(`${label} must be positive`);
  if (nonnegative && normalized < 0) throw new RangeError(`${label} must be nonnegative`);
  return normalized;
}

function rootSumSquares(values) {
  return Math.sqrt(values.filter(Number.isFinite).reduce((sum, value) => sum + value * value, 0));
}

export function normalizedCommittedTransition(raw) {
  const eventDirection = requiredText(raw?.eventDirection, "event direction");
  if (!["attach", "detach"].includes(eventDirection)) {
    throw new Error("event direction must be attach or detach");
  }
  const energyDeltaElectronVolt = optionalFinite(raw.energyDeltaElectronVolt, "energy delta");
  const energyDeltaUncertaintyElectronVolt = optionalFinite(raw.energyDeltaUncertaintyElectronVolt,
    "energy-delta uncertainty", { nonnegative: true });
  if ((energyDeltaElectronVolt == null) !== (energyDeltaUncertaintyElectronVolt == null)) {
    throw new Error("energy delta and its uncertainty must be supplied together");
  }
  const thermodynamicFields = {
    thermodynamicEvidenceSha256: optionalSha(raw.thermodynamicEvidenceSha256,
      "thermodynamic evidence SHA-256"),
    freeEnergySettingsSha256: optionalSha(raw.freeEnergySettingsSha256,
      "free-energy settings SHA-256"),
    chemicalPotentialSettingsSha256: optionalSha(raw.chemicalPotentialSettingsSha256,
      "chemical-potential settings SHA-256"),
    thermodynamicTemperatureKelvin: optionalFinite(raw.thermodynamicTemperatureKelvin,
      "thermodynamic temperature", { positive: true }),
    systemFreeEnergyDeltaElectronVolt: optionalFinite(raw.systemFreeEnergyDeltaElectronVolt,
      "system free-energy delta"),
    systemFreeEnergyDeltaUncertaintyElectronVolt: optionalFinite(
      raw.systemFreeEnergyDeltaUncertaintyElectronVolt,
      "system free-energy uncertainty", { nonnegative: true }),
    reservoirChemicalWorkElectronVolt: optionalFinite(raw.reservoirChemicalWorkElectronVolt,
      "reservoir chemical work"),
    reservoirChemicalWorkUncertaintyElectronVolt: optionalFinite(
      raw.reservoirChemicalWorkUncertaintyElectronVolt,
      "reservoir chemical-work uncertainty", { nonnegative: true }),
    grandPotentialDeltaElectronVolt: optionalFinite(raw.grandPotentialDeltaElectronVolt,
      "grand-potential delta"),
    grandPotentialDeltaUncertaintyElectronVolt: optionalFinite(
      raw.grandPotentialDeltaUncertaintyElectronVolt,
      "grand-potential uncertainty", { nonnegative: true }),
  };
  const thermodynamicFieldCount = Object.values(thermodynamicFields)
    .filter((value) => value != null).length;
  if (thermodynamicFieldCount !== 0
      && thermodynamicFieldCount !== Object.keys(thermodynamicFields).length) {
    throw new Error("grand-canonical transition evidence must be complete or absent");
  }
  const rawSpeciesDelta = Object.entries(raw.speciesDelta || {})
    .map(([species, delta]) => [requiredText(species, "species-delta key"), Number(delta)]);
  if (rawSpeciesDelta.some(([, delta]) => !Number.isInteger(delta) || delta === 0)) {
    throw new Error("every species delta must be a nonzero integer");
  }
  const speciesDelta = Object.fromEntries(rawSpeciesDelta
    .sort(([first], [second]) => first.localeCompare(second)));
  if (thermodynamicFieldCount && !Object.keys(speciesDelta).length) {
    throw new Error("grand-canonical transition evidence needs a nonempty integer species delta");
  }
  return {
    schema: "gcts-committed-reversible-transition-v1",
    eventId: requiredText(raw.eventId, "event ID"),
    candidateId: requiredText(raw.candidateId, "candidate ID"),
    requestSha256: requiredSha(raw.requestSha256, "request SHA-256"),
    responseSha256: requiredSha(raw.responseSha256, "response SHA-256"),
    eventDirection,
    initialGeometrySha256: requiredSha(raw.initialGeometrySha256, "initial geometry SHA-256"),
    finalGeometrySha256: requiredSha(raw.finalGeometrySha256, "final geometry SHA-256"),
    committedStateSha256: requiredSha(raw.committedStateSha256, "committed state SHA-256"),
    exactFinalGeometryReproduced: raw.exactFinalGeometryReproduced === true,
    barrierElectronVolt: optionalFinite(raw.barrierElectronVolt, "barrier", { nonnegative: true }),
    barrierUncertaintyElectronVolt: optionalFinite(raw.barrierUncertaintyElectronVolt,
      "barrier uncertainty", { nonnegative: true }),
    energyDeltaElectronVolt,
    energyDeltaUncertaintyElectronVolt,
    attemptFrequencyPerSecond: optionalFinite(raw.attemptFrequencyPerSecond,
      "attempt frequency", { positive: true }),
    attemptFrequencyUncertaintyLog10: optionalFinite(raw.attemptFrequencyUncertaintyLog10,
      "attempt-frequency uncertainty", { nonnegative: true }),
    logRatePerSecond: optionalFinite(raw.logRatePerSecond, "log rate"),
    temperatureKelvin: optionalFinite(raw.temperatureKelvin, "temperature", { positive: true }),
    methodSettingsSha256: requiredSha(raw.methodSettingsSha256, "method settings SHA-256"),
    prefactorSettingsSha256: raw.prefactorSettingsSha256 == null ? null
      : requiredSha(raw.prefactorSettingsSha256, "prefactor settings SHA-256"),
    speciesDelta,
    ...thermodynamicFields,
    targetUsed: false,
  };
}

export function auditMicroscopicInversePair(firstRaw, secondRaw) {
  const first = normalizedCommittedTransition(firstRaw);
  const second = normalizedCommittedTransition(secondRaw);
  const oppositeDirections = first.eventDirection !== second.eventDirection;
  const geometryCycleClosed = first.initialGeometrySha256 === second.finalGeometrySha256
    && first.finalGeometrySha256 === second.initialGeometrySha256;
  const exactCommittedStates = first.exactFinalGeometryReproduced
    && second.exactFinalGeometryReproduced
    && first.finalGeometrySha256 === first.committedStateSha256
    && second.finalGeometrySha256 === second.committedStateSha256;
  const energyEvidenceComplete = [first.energyDeltaElectronVolt,
    first.energyDeltaUncertaintyElectronVolt, second.energyDeltaElectronVolt,
    second.energyDeltaUncertaintyElectronVolt].every(Number.isFinite);
  const barrierEvidenceComplete = [first.barrierElectronVolt,
    first.barrierUncertaintyElectronVolt, second.barrierElectronVolt,
    second.barrierUncertaintyElectronVolt].every(Number.isFinite);
  const energyDeltaCycleResidualElectronVolt = energyEvidenceComplete
    ? first.energyDeltaElectronVolt + second.energyDeltaElectronVolt : null;
  const energyDeltaCycleUncertaintyElectronVolt = energyEvidenceComplete
    ? rootSumSquares([first.energyDeltaUncertaintyElectronVolt,
      second.energyDeltaUncertaintyElectronVolt]) : null;
  const transitionStateClosureResidualElectronVolt = energyEvidenceComplete && barrierEvidenceComplete
    ? first.barrierElectronVolt - second.barrierElectronVolt - first.energyDeltaElectronVolt : null;
  const transitionStateClosureUncertaintyElectronVolt = energyEvidenceComplete && barrierEvidenceComplete
    ? rootSumSquares([first.barrierUncertaintyElectronVolt, second.barrierUncertaintyElectronVolt,
      first.energyDeltaUncertaintyElectronVolt]) : null;
  const withinThreeSigma = (residual, uncertainty) => Number.isFinite(residual)
    && Number.isFinite(uncertainty) && Math.abs(residual) <= 3 * Math.max(uncertainty, 1e-12);
  const energyDeltaCyclePassed = withinThreeSigma(energyDeltaCycleResidualElectronVolt,
    energyDeltaCycleUncertaintyElectronVolt);
  const transitionStateClosurePassed = withinThreeSigma(transitionStateClosureResidualElectronVolt,
    transitionStateClosureUncertaintyElectronVolt);
  const sameBarrierMethod = first.methodSettingsSha256 === second.methodSettingsSha256;
  const samePrefactorMethod = first.prefactorSettingsSha256 != null
    && first.prefactorSettingsSha256 === second.prefactorSettingsSha256;
  const sameTemperature = Number.isFinite(first.temperatureKelvin)
    && first.temperatureKelvin === second.temperatureKelvin;
  const rateRatioAvailable = sameTemperature && Number.isFinite(first.logRatePerSecond)
    && Number.isFinite(second.logRatePerSecond);
  const grandCanonicalEvidenceComplete = [first, second].every((record) =>
    record.thermodynamicEvidenceSha256 != null
    && Number.isFinite(record.grandPotentialDeltaElectronVolt)
    && Number.isFinite(record.grandPotentialDeltaUncertaintyElectronVolt));
  const transferredSpecies = [...new Set([...Object.keys(first.speciesDelta),
    ...Object.keys(second.speciesDelta)])].sort();
  const speciesTransferReversed = transferredSpecies.length > 0
    && transferredSpecies.every((species) => (first.speciesDelta[species] || 0)
      + (second.speciesDelta[species] || 0) === 0);
  const sameThermodynamicSettings = grandCanonicalEvidenceComplete
    && first.freeEnergySettingsSha256 === second.freeEnergySettingsSha256
    && first.chemicalPotentialSettingsSha256 === second.chemicalPotentialSettingsSha256;
  const thermodynamicTemperatureMatched = grandCanonicalEvidenceComplete && sameTemperature
    && first.thermodynamicTemperatureKelvin === second.thermodynamicTemperatureKelvin
    && first.thermodynamicTemperatureKelvin === first.temperatureKelvin;
  const grandPotentialCycleResidualElectronVolt = grandCanonicalEvidenceComplete
    ? first.grandPotentialDeltaElectronVolt + second.grandPotentialDeltaElectronVolt : null;
  const grandPotentialCycleUncertaintyElectronVolt = grandCanonicalEvidenceComplete
    ? rootSumSquares([first.grandPotentialDeltaUncertaintyElectronVolt,
      second.grandPotentialDeltaUncertaintyElectronVolt]) : null;
  const grandPotentialCyclePassed = withinThreeSigma(grandPotentialCycleResidualElectronVolt,
    grandPotentialCycleUncertaintyElectronVolt);
  const inverseThermalEnergy = thermodynamicTemperatureMatched
    ? 1 / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * first.temperatureKelvin) : null;
  const localBalanceLogResidual = grandCanonicalEvidenceComplete && rateRatioAvailable
    && Number.isFinite(inverseThermalEnergy)
    ? first.logRatePerSecond - second.logRatePerSecond
      + first.grandPotentialDeltaElectronVolt * inverseThermalEnergy : null;
  const localBalancePredictedLogRateRatio = grandCanonicalEvidenceComplete
    && Number.isFinite(inverseThermalEnergy)
    ? -first.grandPotentialDeltaElectronVolt * inverseThermalEnergy : null;
  const logRateUncertainty = (record) => Number.isFinite(inverseThermalEnergy)
    && Number.isFinite(record.barrierUncertaintyElectronVolt)
    && Number.isFinite(record.attemptFrequencyUncertaintyLog10)
    ? rootSumSquares([record.barrierUncertaintyElectronVolt * inverseThermalEnergy,
      record.attemptFrequencyUncertaintyLog10 * Math.LN10]) : null;
  const firstLogRateUncertainty = logRateUncertainty(first);
  const secondLogRateUncertainty = logRateUncertainty(second);
  const localBalanceLogUncertainty = Number.isFinite(localBalanceLogResidual)
    && Number.isFinite(firstLogRateUncertainty) && Number.isFinite(secondLogRateUncertainty)
    ? rootSumSquares([firstLogRateUncertainty, secondLogRateUncertainty,
      first.grandPotentialDeltaUncertaintyElectronVolt * inverseThermalEnergy]) : null;
  const localBalanceResidualPassed = withinThreeSigma(localBalanceLogResidual,
    localBalanceLogUncertainty);
  const microscopicPathClosurePassed = oppositeDirections && geometryCycleClosed && exactCommittedStates
    && sameBarrierMethod && energyDeltaCyclePassed && transitionStateClosurePassed;
  return {
    schema: "gcts-microscopic-inverse-pair-audit-v1",
    firstEventId: first.eventId,
    secondEventId: second.eventId,
    oppositeDirections,
    geometryCycleClosed,
    exactCommittedStates,
    sameBarrierMethod,
    samePrefactorMethod,
    sameTemperature,
    energyEvidenceComplete,
    barrierEvidenceComplete,
    energyDeltaCycleResidualElectronVolt,
    energyDeltaCycleUncertaintyElectronVolt,
    energyDeltaCyclePassed,
    transitionStateClosureResidualElectronVolt,
    transitionStateClosureUncertaintyElectronVolt,
    transitionStateClosurePassed,
    logRateRatio: rateRatioAvailable ? first.logRatePerSecond - second.logRatePerSecond : null,
    rateRatioAvailable,
    microscopicPathClosurePassed,
    grandCanonicalEvidenceComplete,
    speciesTransferReversed,
    sameThermodynamicSettings,
    thermodynamicTemperatureMatched,
    grandPotentialCycleResidualElectronVolt,
    grandPotentialCycleUncertaintyElectronVolt,
    grandPotentialCyclePassed,
    localBalanceLogResidual,
    localBalancePredictedLogRateRatio,
    localBalanceLogUncertainty,
    localBalanceResidualPassed,
    finitePairLocalBalancePassed: microscopicPathClosurePassed && speciesTransferReversed
      && sameThermodynamicSettings
      && thermodynamicTemperatureMatched && grandPotentialCyclePassed
      && localBalanceResidualPassed,
    thermodynamicDetailedBalanceCertified: false,
    globalDetailedBalanceCertified: false,
    reservoirChemicalPotentialUsed: grandCanonicalEvidenceComplete,
    equilibriumConstantInferred: false,
    targetUsed: false,
    claimBoundary: "Exact reversed state hashes establish a microscopic geometry cycle. Barrier/reaction-energy closure checks one method-specific transition-state identity. Optional system free energies and chemical potentials can test the local-balance equation for this finite pair within reported uncertainty. None of these audits proves mechanism completeness, global detailed balance, an equilibrium constant, or an equilibrium ensemble.",
  };
}

export function appendCommittedTransition(history, raw, { maximumRecords = 128 } = {}) {
  const transition = normalizedCommittedTransition(raw);
  if (!Number.isInteger(maximumRecords) || maximumRecords < 2) {
    throw new RangeError("maximumRecords must be an integer of at least two");
  }
  const normalizedHistory = (Array.isArray(history) ? history : [])
    .map(normalizedCommittedTransition);
  if (normalizedHistory.some((record) => record.eventId === transition.eventId)) {
    throw new Error(`duplicate committed transition ${transition.eventId}`);
  }
  const inverse = [...normalizedHistory].reverse().find((record) =>
    record.eventDirection !== transition.eventDirection
    && record.initialGeometrySha256 === transition.finalGeometrySha256
    && record.finalGeometrySha256 === transition.initialGeometrySha256
    && record.exactFinalGeometryReproduced && transition.exactFinalGeometryReproduced) || null;
  const inverseAudit = inverse ? auditMicroscopicInversePair(inverse, transition) : null;
  const nextHistory = [...normalizedHistory, transition].slice(-maximumRecords);
  return {
    history: nextHistory,
    transition,
    inverseEventId: inverse?.eventId || null,
    inverseAudit,
    exactInversePairCount: nextHistory.filter((record, index) => nextHistory.slice(0, index)
      .some((prior) => prior.eventDirection !== record.eventDirection
        && prior.initialGeometrySha256 === record.finalGeometrySha256
        && prior.finalGeometrySha256 === record.initialGeometrySha256
        && prior.exactFinalGeometryReproduced && record.exactFinalGeometryReproduced)).length,
    targetUsed: false,
  };
}
