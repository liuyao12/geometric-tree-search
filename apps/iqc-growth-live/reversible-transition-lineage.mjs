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

function normalizedTemperatureApplicability(raw) {
  if (raw == null) return null;
  const scope = requiredText(raw.scope, "temperature applicability scope");
  if (scope === "single-temperature") {
    if (raw.minimumKelvin != null || raw.maximumKelvin != null
        || raw.externallyAuthorized === true
        || raw.barrierAndPrefactorAssumedConstant === true) {
      throw new Error("single-temperature applicability cannot authorize a temperature interval");
    }
    return { scope, minimumKelvin: null, maximumKelvin: null,
      externallyAuthorized: false, barrierAndPrefactorAssumedConstant: false };
  }
  if (scope !== "bounded-constant-htst") {
    throw new Error("temperature applicability scope must be single-temperature or bounded-constant-htst");
  }
  const minimumKelvin = optionalFinite(raw.minimumKelvin,
    "minimum applicable temperature", { positive: true });
  const maximumKelvin = optionalFinite(raw.maximumKelvin,
    "maximum applicable temperature", { positive: true });
  if (!(minimumKelvin >= 1 && maximumKelvin <= 5000 && minimumKelvin < maximumKelvin)
      || raw.externallyAuthorized !== true
      || raw.barrierAndPrefactorAssumedConstant !== true) {
    throw new Error("bounded constant-HTST applicability needs an authorized 1..5000 K interval and constant barrier/prefactor assumption");
  }
  return { scope, minimumKelvin, maximumKelvin,
    externallyAuthorized: true, barrierAndPrefactorAssumedConstant: true };
}

function rootSumSquares(values) {
  return Math.sqrt(values.filter(Number.isFinite).reduce((sum, value) => sum + value * value, 0));
}

function normalizedStateGeometricDescriptor(raw, label) {
  if (raw == null) return null;
  const atomCount = optionalFinite(raw.atomCount, `${label} atom count`, { nonnegative: true });
  if (!Number.isInteger(atomCount) || atomCount < 2) {
    throw new Error(`${label} atom count must be an integer of at least two`);
  }
  const speciesCounts = Object.fromEntries(Object.entries(raw.speciesCounts || {})
    .map(([species, count]) => [requiredText(species, `${label} species`), Number(count)])
    .sort(([first], [second]) => first.localeCompare(second)));
  if (!Object.keys(speciesCounts).length || Object.values(speciesCounts).some((count) =>
    !Number.isInteger(count) || count <= 0)
      || Object.values(speciesCounts).reduce((sum, count) => sum + count, 0) !== atomCount) {
    throw new Error(`${label} species counts must be positive integers summing to atom count`);
  }
  const contactReach = optionalFinite(raw.contactReach, `${label} contact reach`, { positive: true });
  if (!(contactReach > 1)) throw new RangeError(`${label} contact reach must exceed one`);
  const medianNearestNeighborAngstrom = optionalFinite(raw.medianNearestNeighborAngstrom,
    `${label} median nearest-neighbor distance`, { positive: true });
  const cutoffAngstrom = optionalFinite(raw.cutoffAngstrom, `${label} cutoff`, { positive: true });
  if (Math.abs(cutoffAngstrom - contactReach * medianNearestNeighborAngstrom) > 1e-10) {
    throw new Error(`${label} cutoff must equal contact reach times median nearest-neighbor distance`);
  }
  const contactCount = optionalFinite(raw.contactCount, `${label} contact count`,
    { nonnegative: true });
  const minimumCoordination = optionalFinite(raw.minimumCoordination,
    `${label} minimum coordination`, { nonnegative: true });
  const maximumCoordination = optionalFinite(raw.maximumCoordination,
    `${label} maximum coordination`, { nonnegative: true });
  if (![contactCount, minimumCoordination, maximumCoordination].every(Number.isInteger)) {
    throw new Error(`${label} contact and coordination extrema must be integers`);
  }
  const meanCoordination = optionalFinite(raw.meanCoordination,
    `${label} mean coordination`, { nonnegative: true });
  const coordinationStandardDeviation = optionalFinite(raw.coordinationStandardDeviation,
    `${label} coordination standard deviation`, { nonnegative: true });
  if (Math.abs(meanCoordination * atomCount - 2 * contactCount) > 1e-8
      || minimumCoordination > meanCoordination || maximumCoordination < meanCoordination) {
    throw new Error(`${label} coordination moments are inconsistent with its contact graph`);
  }
  const sameSpeciesContactFraction = contactCount ? optionalFinite(raw.sameSpeciesContactFraction,
    `${label} same-species contact fraction`, { nonnegative: true }) : null;
  if (sameSpeciesContactFraction != null && sameSpeciesContactFraction > 1) {
    throw new RangeError(`${label} same-species contact fraction cannot exceed one`);
  }
  const speciesPairContactFractions = Object.fromEntries(Object.entries(
    raw.speciesPairContactFractions || {}).map(([pair, fraction]) =>
    [requiredText(pair, `${label} species-pair contact`), Number(fraction)])
    .sort(([first], [second]) => first.localeCompare(second)));
  if (Object.values(speciesPairContactFractions).some((fraction) =>
    !Number.isFinite(fraction) || fraction < 0 || fraction > 1)
      || (contactCount && Math.abs(Object.values(speciesPairContactFractions)
        .reduce((sum, fraction) => sum + fraction, 0) - 1) > 1e-10)
      || (!contactCount && Object.keys(speciesPairContactFractions).length)) {
    throw new Error(`${label} species-pair contact fractions are invalid`);
  }
  const steinhardtQ4 = contactCount ? optionalFinite(raw.steinhardtQ4,
    `${label} Steinhardt Q4`, { nonnegative: true }) : null;
  const steinhardtQ6 = contactCount ? optionalFinite(raw.steinhardtQ6,
    `${label} Steinhardt Q6`, { nonnegative: true }) : null;
  if ([steinhardtQ4, steinhardtQ6].some((value) => value != null && value > 1 + 1e-10)) {
    throw new RangeError(`${label} Steinhardt order cannot exceed one`);
  }
  return {
    schema: "gcts-global-geometric-state-descriptor-v1",
    atomCount, speciesCounts, contactReach, medianNearestNeighborAngstrom, cutoffAngstrom,
    contactCount, meanCoordination, coordinationStandardDeviation,
    minimumCoordination, maximumCoordination, sameSpeciesContactFraction,
    speciesPairContactFractions, steinhardtQ4, steinhardtQ6,
    finiteObservationBoundaryIncluded: true, periodicImagesAdded: false,
    targetUsed: false, rotationallyInvariant: true, chemicalBondClaimed: false,
    thermodynamicOrderParameterClaimed: false,
  };
}

export function normalizedCommittedTransition(raw) {
  const eventDirection = requiredText(raw?.eventDirection, "event direction");
  if (!["attach", "detach", "hop", "exchange"].includes(eventDirection)) {
    throw new Error("event direction must be attach, detach, hop, or exchange");
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
  const initialAtomCount = raw.initialAtomCount == null ? null
    : optionalFinite(raw.initialAtomCount, "initial atom count", { nonnegative: true });
  const finalAtomCount = raw.finalAtomCount == null ? null
    : optionalFinite(raw.finalAtomCount, "final atom count", { nonnegative: true });
  if ((initialAtomCount == null) !== (finalAtomCount == null)
      || (initialAtomCount != null && (!Number.isInteger(initialAtomCount)
        || !Number.isInteger(finalAtomCount)))) {
    throw new Error("initial and final atom counts must be supplied together as nonnegative integers");
  }
  if (initialAtomCount != null && Object.keys(speciesDelta).length
      && finalAtomCount - initialAtomCount
        !== Object.values(speciesDelta).reduce((sum, delta) => sum + delta, 0)) {
    throw new Error("atom-count change must equal the summed species transfer");
  }
  if (thermodynamicFieldCount && !Object.keys(speciesDelta).length && eventDirection !== "hop") {
    throw new Error("grand-canonical transition evidence needs a nonempty integer species delta");
  }
  const geometricPathObservable = raw.geometricPathObservable == null ? null : (() => {
    const source = raw.geometricPathObservable;
    const contactReach = optionalFinite(source.contactReach, "geometric contact reach",
      { positive: true });
    if (!(contactReach > 1)) throw new RangeError("geometric contact reach must exceed one");
    const contactResolved = source.contactResolved === true;
    const referenceLengthAngstrom = optionalFinite(source.referenceLengthAngstrom,
      "geometric reference length", { positive: true });
    const netContactDelta = optionalFinite(source.netContactDelta, "net geometric contact delta");
    const netFormedContactCount = optionalFinite(source.netFormedContactCount,
      "formed geometric contact count", { nonnegative: true });
    const netBrokenContactCount = optionalFinite(source.netBrokenContactCount,
      "broken geometric contact count", { nonnegative: true });
    const initialContactCount = optionalFinite(source.initialContactCount,
      "initial geometric contact count", { nonnegative: true });
    const finalContactCount = optionalFinite(source.finalContactCount,
      "final geometric contact count", { nonnegative: true });
    const initialMeanDynamicCoordination = optionalFinite(source.initialMeanDynamicCoordination,
      "initial mean dynamic coordination", { nonnegative: true });
    const finalMeanDynamicCoordination = optionalFinite(source.finalMeanDynamicCoordination,
      "final mean dynamic coordination", { nonnegative: true });
    const meanDynamicCoordinationDelta = optionalFinite(source.meanDynamicCoordinationDelta,
      "mean dynamic coordination delta");
    const maximumAdjacentDisplacementAngstrom = optionalFinite(
      source.maximumAdjacentDisplacementAngstrom, "maximum adjacent displacement",
      { nonnegative: true });
    const geometricCharacter = source.geometricCharacter == null ? null
      : requiredText(source.geometricCharacter, "geometric character");
    const integerCounts = [netContactDelta, netFormedContactCount, netBrokenContactCount,
      initialContactCount, finalContactCount];
    if (integerCounts.some((value) => value != null && !Number.isInteger(value))) {
      throw new Error("geometric contact counts and deltas must be integers");
    }
    const resolvedFields = [referenceLengthAngstrom, netContactDelta, netFormedContactCount,
      netBrokenContactCount, initialContactCount, finalContactCount,
      initialMeanDynamicCoordination, finalMeanDynamicCoordination,
      meanDynamicCoordinationDelta, geometricCharacter];
    if (contactResolved && resolvedFields.some((value) => value == null)) {
      throw new Error("resolved geometric path evidence must include all contact observables");
    }
    if (!contactResolved && resolvedFields.some((value) => value != null)) {
      throw new Error("unresolved geometric path evidence cannot carry contact observables");
    }
    if (contactResolved && netContactDelta !== finalContactCount - initialContactCount) {
      throw new Error("net contact delta must match final minus initial contact count");
    }
    if (contactResolved && netContactDelta !== netFormedContactCount - netBrokenContactCount) {
      throw new Error("net contact delta must match formed minus broken contacts");
    }
    if (contactResolved && Math.abs(meanDynamicCoordinationDelta
      - (finalMeanDynamicCoordination - initialMeanDynamicCoordination)) > 1e-10) {
      throw new Error("coordination delta must match final minus initial coordination");
    }
    return {
      schema: "gcts-committed-path-geometric-observable-v1",
      contactReach, contactResolved, referenceLengthAngstrom,
      netContactDelta, netFormedContactCount, netBrokenContactCount,
      initialContactCount, finalContactCount,
      initialMeanDynamicCoordination, finalMeanDynamicCoordination,
      meanDynamicCoordinationDelta, maximumAdjacentDisplacementAngstrom,
      geometricCharacter,
      targetUsed: false, chemicalBondClaimed: false, physicalTimeInferred: false,
    };
  })();
  const initialStateGeometricDescriptor = normalizedStateGeometricDescriptor(
    raw.initialStateGeometricDescriptor, "initial global geometric descriptor");
  const finalStateGeometricDescriptor = normalizedStateGeometricDescriptor(
    raw.finalStateGeometricDescriptor, "final global geometric descriptor");
  if ((initialStateGeometricDescriptor == null) !== (finalStateGeometricDescriptor == null)) {
    throw new Error("initial and final global geometric descriptors must be supplied together");
  }
  if (initialStateGeometricDescriptor
      && (initialStateGeometricDescriptor.atomCount !== initialAtomCount
        || finalStateGeometricDescriptor.atomCount !== finalAtomCount
        || initialStateGeometricDescriptor.contactReach !== finalStateGeometricDescriptor.contactReach)) {
    throw new Error("global geometric descriptors must match transition atom counts and contact reach");
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
    temperatureApplicability: normalizedTemperatureApplicability(raw.temperatureApplicability),
    methodSettingsSha256: requiredSha(raw.methodSettingsSha256, "method settings SHA-256"),
    prefactorSettingsSha256: raw.prefactorSettingsSha256 == null ? null
      : requiredSha(raw.prefactorSettingsSha256, "prefactor settings SHA-256"),
    speciesDelta,
    initialAtomCount,
    finalAtomCount,
    geometricPathObservable,
    initialStateGeometricDescriptor,
    finalStateGeometricDescriptor,
    ...thermodynamicFields,
    targetUsed: false,
  };
}

export function auditMicroscopicInversePair(firstRaw, secondRaw) {
  const first = normalizedCommittedTransition(firstRaw);
  const second = normalizedCommittedTransition(secondRaw);
  const oppositeDirections = first.eventDirection !== second.eventDirection;
  const massConservingHopPair = first.eventDirection === "hop"
    && second.eventDirection === "hop";
  const sameDirectionMassConservingPair = ["hop", "exchange"].includes(first.eventDirection)
    && first.eventDirection === second.eventDirection;
  const directionPairCanReverse = oppositeDirections || sameDirectionMassConservingPair;
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
  const speciesTransferReversed = (first.eventDirection === "hop"
      && second.eventDirection === "hop" && transferredSpecies.length === 0)
    || (transferredSpecies.length > 0 && transferredSpecies.every((species) =>
      (first.speciesDelta[species] || 0) + (second.speciesDelta[species] || 0) === 0));
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
  const geometricPathEvidenceComplete = first.geometricPathObservable?.contactResolved === true
    && second.geometricPathObservable?.contactResolved === true;
  const sameGeometricContactDefinition = geometricPathEvidenceComplete
    && first.geometricPathObservable.contactReach === second.geometricPathObservable.contactReach
    && Math.abs(first.geometricPathObservable.referenceLengthAngstrom
      - second.geometricPathObservable.referenceLengthAngstrom) <= 1e-10;
  const geometricContactCycleResidual = sameGeometricContactDefinition
    ? first.geometricPathObservable.netContactDelta
      + second.geometricPathObservable.netContactDelta : null;
  const geometricCoordinationCycleResidual = sameGeometricContactDefinition
    ? first.geometricPathObservable.meanDynamicCoordinationDelta
      + second.geometricPathObservable.meanDynamicCoordinationDelta : null;
  const geometricPathObservableClosurePassed = sameGeometricContactDefinition
    && Math.abs(geometricContactCycleResidual) <= 1e-10
    && Math.abs(geometricCoordinationCycleResidual) <= 1e-10;
  const microscopicPathClosurePassed = directionPairCanReverse && geometryCycleClosed && exactCommittedStates
    && sameBarrierMethod && energyDeltaCyclePassed && transitionStateClosurePassed;
  return {
    schema: "gcts-microscopic-inverse-pair-audit-v1",
    firstEventId: first.eventId,
    secondEventId: second.eventId,
    oppositeDirections,
    massConservingHopPair,
    directionPairCanReverse,
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
    geometricPathEvidenceComplete,
    sameGeometricContactDefinition,
    geometricContactCycleResidual,
    geometricCoordinationCycleResidual,
    geometricPathObservableClosurePassed,
    finitePairLocalBalancePassed: microscopicPathClosurePassed && speciesTransferReversed
      && sameThermodynamicSettings
      && thermodynamicTemperatureMatched && grandPotentialCyclePassed
      && localBalanceResidualPassed,
    thermodynamicDetailedBalanceCertified: false,
    globalDetailedBalanceCertified: false,
    reservoirChemicalPotentialUsed: grandCanonicalEvidenceComplete,
    equilibriumConstantInferred: false,
    targetUsed: false,
    claimBoundary: "Exact reversed state hashes establish a microscopic geometry cycle. Barrier/reaction-energy closure checks one method-specific transition-state identity. A separately matched contact definition can test reversal of local geometric contact and coordination changes. Optional system free energies and chemical potentials can test the local-balance equation for this finite pair within reported uncertainty. None of these audits proves mechanism completeness, global detailed balance, an equilibrium constant, or an equilibrium ensemble.",
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
    (record.eventDirection !== transition.eventDirection
      || (["hop", "exchange"].includes(record.eventDirection)
        && record.eventDirection === transition.eventDirection))
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
      .some((prior) => (prior.eventDirection !== record.eventDirection
        || (["hop", "exchange"].includes(prior.eventDirection)
          && prior.eventDirection === record.eventDirection))
        && prior.initialGeometrySha256 === record.finalGeometrySha256
        && prior.finalGeometrySha256 === record.initialGeometrySha256
        && prior.exactFinalGeometryReproduced && record.exactFinalGeometryReproduced)).length,
    targetUsed: false,
  };
}
