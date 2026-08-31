const SHA256 = /^[a-f0-9]{64}$/i;

function requiredText(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function requiredSha(value, label) {
  const normalized = requiredText(value, label);
  if (!SHA256.test(normalized)) throw new TypeError(`${label} must be a SHA-256 digest`);
  return normalized.toLowerCase();
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
    microscopicPathClosurePassed: oppositeDirections && geometryCycleClosed && exactCommittedStates
      && sameBarrierMethod && energyDeltaCyclePassed && transitionStateClosurePassed,
    thermodynamicDetailedBalanceCertified: false,
    reservoirChemicalPotentialUsed: false,
    equilibriumConstantInferred: false,
    targetUsed: false,
    claimBoundary: "Exact reversed state hashes establish a microscopic geometry cycle. Barrier/reaction-energy closure checks one method-specific transition-state identity within reported uncertainty. Neither result supplies reservoir chemical potentials, free energies, mechanism completeness, detailed balance, an equilibrium constant, or an equilibrium ensemble.",
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
