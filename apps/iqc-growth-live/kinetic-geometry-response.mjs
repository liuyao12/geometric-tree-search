import { analyzeActionPathMechanism }
  from "./action-path-mechanism.mjs?v=20260831-388";
import { buildFrozenKineticCompetition }
  from "./frozen-frontier-kinetics.mjs?v=20260831-388";
import { buildTemperatureProgrammedKinetics }
  from "./temperature-programmed-kinetics.mjs?v=20260831-388";

export const KINETIC_GEOMETRY_CHARACTERS = Object.freeze([
  "contact-forming", "contact-breaking", "contact exchange / reconstructive",
  "displacive at this contact reach",
]);

function probabilityMass(records, predicate) {
  return records.filter(predicate).reduce((sum, record) =>
    sum + record.probabilityWithinFrozenCatalog, 0);
}

function logSumExp(values) {
  if (!values.length) return -Infinity;
  const maximum = Math.max(...values);
  return maximum + Math.log(values.reduce((sum, value) => sum + Math.exp(value - maximum), 0));
}

function extremalSignedSumSign(records, observable, threshold, maximize) {
  const positive = []; const negative = [];
  records.forEach((record) => {
    const coefficient = observable(record) - threshold;
    if (Math.abs(coefficient) < 1e-15) return;
    const favorCoefficient = maximize ? coefficient > 0 : coefficient < 0;
    const logRate = Math.LN10 * (favorCoefficient
      ? record.log10RateUpperPerSecond : record.log10RateLowerPerSecond);
    const term = logRate + Math.log(Math.abs(coefficient));
    (coefficient > 0 ? positive : negative).push(term);
  });
  const positiveLog = logSumExp(positive); const negativeLog = logSumExp(negative);
  if (positiveLog === negativeLog) return 0;
  return positiveLog > negativeLog ? 1 : -1;
}

export function rateBoxObservableEnvelope(records, observable) {
  if (!Array.isArray(records) || !records.length) {
    throw new TypeError("a rate-box envelope needs at least one event");
  }
  const values = records.map((record) => Number(observable(record)));
  if (values.some((value) => !Number.isFinite(value))
      || records.some((record) => !Number.isFinite(record.log10RateLowerPerSecond)
        || !Number.isFinite(record.log10RateUpperPerSecond)
        || record.log10RateLowerPerSecond > record.log10RateUpperPerSecond)) {
    throw new TypeError("rate-box observables and logarithmic rate bounds must be finite and ordered");
  }
  const domainMinimum = Math.min(...values); const domainMaximum = Math.max(...values);
  if (domainMinimum === domainMaximum) return [domainMinimum, domainMaximum];
  const solve = (maximize) => {
    let low = domainMinimum; let high = domainMaximum;
    for (let iteration = 0; iteration < 90; iteration += 1) {
      const middle = (low + high) / 2;
      const sign = extremalSignedSumSign(records, observable, middle, maximize);
      if (maximize ? sign > 0 : sign >= 0) low = middle;
      else high = middle;
    }
    return (low + high) / 2;
  };
  return [solve(false), solve(true)];
}

function transitionIntervals(samples, field) {
  const intervals = [];
  for (let index = 1; index < samples.length; index += 1) {
    if (samples[index - 1][field] === samples[index][field]) continue;
    intervals.push({ from: samples[index - 1][field], to: samples[index][field],
      lowerKelvin: Math.min(samples[index - 1].temperatureKelvin,
        samples[index].temperatureKelvin),
      upperKelvin: Math.max(samples[index - 1].temperatureKelvin,
        samples[index].temperatureKelvin) });
  }
  return intervals;
}

export function buildEventGeometryObservables(record, contactReach = 1.35) {
  if (!record?.pathGeometry?.coordinateBearingImagesValidated) {
    throw new Error(`candidate ${record?.candidateId || "unknown"} lacks a validated coordinate path`);
  }
  const mechanism = analyzeActionPathMechanism(record.pathGeometry, { contactReach });
  const initialMaterialCount = record.pathGeometry.materialCounts[0];
  const finalMaterialCount = record.pathGeometry.materialCounts.at(-1);
  const initialCoordination = mechanism.perImage[0].meanDynamicCoordination;
  const finalCoordination = mechanism.perImage.at(-1).meanDynamicCoordination;
  const initialContactCount = mechanism.perImage[0].contactCount;
  const finalContactCount = mechanism.perImage.at(-1).contactCount;
  return {
    candidateId: record.candidateId,
    eventDirection: record.eventDirection,
    materialAtomDelta: finalMaterialCount - initialMaterialCount,
    contactResolved: mechanism.referenceAvailable,
    netContactDelta: mechanism.referenceAvailable
      ? mechanism.netFormedContactCount - mechanism.netBrokenContactCount : null,
    netFormedContactCount: mechanism.referenceAvailable
      ? mechanism.netFormedContactCount : null,
    netBrokenContactCount: mechanism.referenceAvailable
      ? mechanism.netBrokenContactCount : null,
    initialContactCount: mechanism.referenceAvailable ? initialContactCount : null,
    finalContactCount: mechanism.referenceAvailable ? finalContactCount : null,
    initialMeanDynamicCoordination: mechanism.referenceAvailable ? initialCoordination : null,
    finalMeanDynamicCoordination: mechanism.referenceAvailable ? finalCoordination : null,
    meanDynamicCoordinationDelta: mechanism.referenceAvailable
      ? finalCoordination - initialCoordination : null,
    maximumAdjacentDisplacementAngstrom: record.pathGeometry.maximumSiteDisplacementAngstrom,
    geometricCharacter: mechanism.referenceAvailable ? mechanism.geometricCharacter : null,
    contactReach: mechanism.contactReach,
    referenceLengthAngstrom: mechanism.referenceLengthAngstrom,
  };
}

export function buildKineticGeometryResponse(records, applicability, {
  contactReach = 1.35,
  sampleCount = 41,
} = {}) {
  const temperatureProgram = buildTemperatureProgrammedKinetics(records, applicability,
    { sampleCount });
  if (!temperatureProgram.available) {
    return { schema: 1, available: false, reason: temperatureProgram.reason,
      temperatureProgram, targetUsed: false, candidateSetChanged: false,
      geometricEndpointsChanged: false,
      claimBoundary: "A geometric response is withheld when the bounded temperature program is not externally authorized." };
  }
  const geometry = records.map((record) => buildEventGeometryObservables(record, contactReach));
  const geometryById = new Map(geometry.map((record) => [record.candidateId, record]));
  const samples = temperatureProgram.samples.map((temperatureSample) => {
    const competition = buildFrozenKineticCompetition(records,
      { temperatureKelvin: temperatureSample.temperatureKelvin, mode: "rate-maximum" });
    const weighted = competition.records.map((rate) => ({ ...rate,
      geometry: geometryById.get(rate.candidateId) }));
    const growingProbability = probabilityMass(weighted,
      (record) => record.geometry.materialAtomDelta > 0);
    const shrinkingProbability = probabilityMass(weighted,
      (record) => record.geometry.materialAtomDelta < 0);
    const countPreservingProbability = probabilityMass(weighted,
      (record) => record.geometry.materialAtomDelta === 0);
    const expectedMaterialAtomDeltaPerEvent = weighted.reduce((sum, record) =>
      sum + record.probabilityWithinFrozenCatalog * record.geometry.materialAtomDelta, 0);
    const contactResolvedProbabilityMass = probabilityMass(weighted,
      (record) => record.geometry.contactResolved);
    const contactWeighted = weighted.filter((record) => record.geometry.contactResolved);
    const conditionalExpectedNetContactDeltaPerResolvedEvent = contactResolvedProbabilityMass
      ? contactWeighted.reduce((sum, record) => sum
        + record.probabilityWithinFrozenCatalog * record.geometry.netContactDelta, 0)
        / contactResolvedProbabilityMass : null;
    const conditionalExpectedCoordinationDeltaPerResolvedEvent = contactResolvedProbabilityMass
      ? contactWeighted.reduce((sum, record) => sum
        + record.probabilityWithinFrozenCatalog
          * record.geometry.meanDynamicCoordinationDelta, 0)
        / contactResolvedProbabilityMass : null;
    const expectedMaximumAdjacentDisplacementAngstrom = weighted.reduce((sum, record) =>
      sum + record.probabilityWithinFrozenCatalog
        * record.geometry.maximumAdjacentDisplacementAngstrom, 0);
    const geometricCharacterProbabilityMass = Object.fromEntries(KINETIC_GEOMETRY_CHARACTERS
      .map((character) => [character, probabilityMass(weighted,
        (record) => record.geometry.geometricCharacter === character)]));
    const dominantResolvedGeometricCharacter = contactResolvedProbabilityMass
      ? [...KINETIC_GEOMETRY_CHARACTERS].sort((first, second) =>
        geometricCharacterProbabilityMass[second] - geometricCharacterProbabilityMass[first]
        || first.localeCompare(second))[0] : null;
    const materialAtomDeltaEnvelope = rateBoxObservableEnvelope(weighted,
      (record) => record.geometry.materialAtomDelta);
    const growingProbabilityEnvelope = rateBoxObservableEnvelope(weighted,
      (record) => record.geometry.materialAtomDelta > 0 ? 1 : 0);
    const shrinkingProbabilityEnvelope = rateBoxObservableEnvelope(weighted,
      (record) => record.geometry.materialAtomDelta < 0 ? 1 : 0);
    const countPreservingProbabilityEnvelope = rateBoxObservableEnvelope(weighted,
      (record) => record.geometry.materialAtomDelta === 0 ? 1 : 0);
    const netContactDeltaEnvelope = contactWeighted.length
      ? rateBoxObservableEnvelope(contactWeighted, (record) => record.geometry.netContactDelta)
      : null;
    const coordinationDeltaEnvelope = contactWeighted.length
      ? rateBoxObservableEnvelope(contactWeighted,
        (record) => record.geometry.meanDynamicCoordinationDelta) : null;
    const displacementEnvelopeAngstrom = rateBoxObservableEnvelope(weighted,
      (record) => record.geometry.maximumAdjacentDisplacementAngstrom);
    return {
      temperatureKelvin: temperatureSample.temperatureKelvin,
      fastestCandidateId: temperatureSample.fastestCandidateId,
      fastestEventDirection: temperatureSample.fastestEventDirection,
      growingProbability, shrinkingProbability, countPreservingProbability,
      signedGrowthBias: growingProbability - shrinkingProbability,
      expectedMaterialAtomDeltaPerEvent,
      contactResolvedProbabilityMass,
      conditionalExpectedNetContactDeltaPerResolvedEvent,
      conditionalExpectedCoordinationDeltaPerResolvedEvent,
      expectedMaximumAdjacentDisplacementAngstrom,
      rateBoxEnvelope: {
        expectedMaterialAtomDeltaPerEvent: materialAtomDeltaEnvelope,
        growingProbability: growingProbabilityEnvelope,
        shrinkingProbability: shrinkingProbabilityEnvelope,
        countPreservingProbability: countPreservingProbabilityEnvelope,
        conditionalExpectedNetContactDeltaPerResolvedEvent: netContactDeltaEnvelope,
        conditionalExpectedCoordinationDeltaPerResolvedEvent: coordinationDeltaEnvelope,
        expectedMaximumAdjacentDisplacementAngstrom: displacementEnvelopeAngstrom,
      },
      geometricCharacterProbabilityMass,
      dominantResolvedGeometricCharacter,
      log10TotalRatePerSecond: competition.log10TotalRatePerSecond,
    };
  });
  return {
    schema: 1,
    available: true,
    model: "finite-catalog one-event kinetic-to-geometric response",
    contactReach: Number(contactReach),
    candidateCount: geometry.length,
    temperatureProgram,
    eventGeometry: geometry,
    samples,
    dominantCharacterCrossovers: transitionIntervals(samples,
      "dominantResolvedGeometricCharacter"),
    targetUsed: false,
    candidateSetChanged: false,
    geometricEndpointsChanged: false,
    physicalTrajectoryIntegrated: false,
    futureFrontierAssumedUnchanged: false,
    adversarialRateIntervalEnvelopeComputed: true,
    rateIntervalAssumption: "independent per-event barrier-plus-prefactor log-rate boxes",
    stochasticUncertaintyPropagatedIntoResponse: false,
    claimBoundary: "This is the nominal expectation for the next event inside one unchanged finite frontier catalog. Contact expectations are conditional on the probability mass with a derived local contact reference. Shaded extrema are adversarial bounds over independent supplied log-rate intervals, not confidence or credible intervals. The response does not keep the frontier fixed after an event, integrate morphology or time, discover missing events, or predict a bulk growth regime.",
  };
}

export function inspectKineticGeometryResponse(response, temperatureKelvin) {
  if (!response?.available || !response.samples.length) return null;
  const value = Number(temperatureKelvin);
  if (!Number.isFinite(value)) throw new TypeError("temperatureKelvin must be finite");
  return [...response.samples].sort((first, second) =>
    Math.abs(first.temperatureKelvin - value) - Math.abs(second.temperatureKelvin - value))[0];
}
