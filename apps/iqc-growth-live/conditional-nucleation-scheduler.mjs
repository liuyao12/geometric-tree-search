const UINT32_RANGE = 0x1_0000_0000;

function positive(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number) || !(number > 0)) {
    throw new TypeError(`${label} must be finite and positive`);
  }
  return number;
}

function integer(value, label, minimum, maximum) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < minimum || number > maximum) {
    throw new RangeError(`${label} must be an integer from ${minimum} to ${maximum}`);
  }
  return number;
}

function mulberry32(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return (((value ^ (value >>> 14)) >>> 0) + .5) / UINT32_RANGE;
  };
}

function exponentialOrInfinity(logValue) {
  if (logValue > Math.log(Number.MAX_VALUE)) return Infinity;
  if (logValue < Math.log(Number.MIN_VALUE)) return 0;
  return Math.exp(logValue);
}

export function buildConditionalNucleationSchedule(rate, options = {}) {
  if (!rate?.conditionalSteadyStateHomogeneousCnt || rate?.targetUsed) {
    throw new Error("accepted target-blind conditional nucleation-rate evidence is required");
  }
  const dimension = Number(rate.intrinsicDimension);
  if (![2, 3].includes(dimension)) throw new RangeError("rate dimension must be 2 or 3");
  const characteristicLengthMetre = positive(options.characteristicLengthMetre,
    "observation length");
  const exposureSeconds = positive(options.exposureSeconds, "exposure time");
  const randomSeed = integer(options.randomSeed ?? 2026, "random seed", 0, 0xffff_ffff);
  const maximumEvents = integer(options.maximumEvents ?? 32, "maximum events", 1, 512);
  const logTotalIntensityPerSecond = Number(rate.logRateDensityPerSi)
    + dimension * Math.log(characteristicLengthMetre);
  if (!Number.isFinite(logTotalIntensityPerSecond)) {
    throw new TypeError("total nucleation intensity must be finite in log space");
  }
  const logExpectedEventCount = logTotalIntensityPerSecond + Math.log(exposureSeconds);
  const expectedEventCount = exponentialOrInfinity(logExpectedEventCount);
  const atLeastOneEventProbability = expectedEventCount === Infinity ? 1
    : -Math.expm1(-expectedEventCount);
  const random = mulberry32(randomSeed);
  const events = [];
  let elapsedSeconds = 0;
  let zeroWaitUnderflowCount = 0;
  while (events.length < maximumEvents) {
    const waitingUniform = random();
    const logWaitingTimeSeconds = Math.log(-Math.log(waitingUniform))
      - logTotalIntensityPerSecond;
    const waitingTimeSeconds = exponentialOrInfinity(logWaitingTimeSeconds);
    if (waitingTimeSeconds === 0) zeroWaitUnderflowCount += 1;
    const eventTimeSeconds = elapsedSeconds + waitingTimeSeconds;
    if (!Number.isFinite(eventTimeSeconds) || eventTimeSeconds > exposureSeconds) break;
    const normalizedPosition = Array.from({ length: dimension }, () => random());
    events.push({
      eventId: `nucleus-${String(events.length + 1).padStart(4, "0")}`,
      eventIndex: events.length,
      waitingUniform,
      waitingTimeSeconds,
      log10WaitingTimeSeconds: logWaitingTimeSeconds / Math.LN10,
      eventTimeSeconds,
      normalizedPosition,
      positionMetre: normalizedPosition.map((coordinate) =>
        coordinate * characteristicLengthMetre),
      atomisticNucleusConstructed: false,
      crystallographicPoseAssigned: false,
      gctsSeedChanged: false,
      targetUsed: false,
    });
    elapsedSeconds = eventTimeSeconds;
  }
  let firstOmittedEventFallsInsideExposure = false;
  let truncationProbe = null;
  if (events.length === maximumEvents) {
    const waitingUniform = random();
    const logWaitingTimeSeconds = Math.log(-Math.log(waitingUniform))
      - logTotalIntensityPerSecond;
    const waitingTimeSeconds = exponentialOrInfinity(logWaitingTimeSeconds);
    firstOmittedEventFallsInsideExposure = elapsedSeconds + waitingTimeSeconds <= exposureSeconds;
    truncationProbe = { waitingUniform, waitingTimeSeconds,
      log10WaitingTimeSeconds: logWaitingTimeSeconds / Math.LN10,
      proposedEventTimeSeconds: elapsedSeconds + waitingTimeSeconds,
      fallsInsideExposure: firstOmittedEventFallsInsideExposure };
  }
  const scheduleTruncated = events.length === maximumEvents
    && firstOmittedEventFallsInsideExposure;
  return {
    schema: "gcts-conditional-nucleation-schedule-v1",
    intrinsicDimension: dimension,
    structureSha256: rate.structureSha256,
    workSha256: rate.workSha256,
    kineticsRequestSha256: rate.kineticsRequestSha256,
    parentPhase: rate.parentPhase,
    nucleusPhase: rate.nucleusPhase,
    temperatureKelvin: rate.temperatureKelvin,
    characteristicLengthMetre,
    observationMeasureSi: characteristicLengthMetre ** dimension,
    exposureSeconds,
    logTotalIntensityPerSecond,
    log10TotalIntensityPerSecond: logTotalIntensityPerSecond / Math.LN10,
    logExpectedEventCount,
    log10ExpectedEventCount: logExpectedEventCount / Math.LN10,
    expectedEventCount,
    atLeastOneEventProbability,
    randomGenerator: "mulberry32",
    randomSeed,
    maximumEvents,
    events,
    scheduledEventCount: events.length,
    firstEventSeconds: events[0]?.eventTimeSeconds ?? null,
    lastEventSeconds: events.at(-1)?.eventTimeSeconds ?? null,
    zeroWaitUnderflowCount,
    truncationProbe,
    firstOmittedEventFallsInsideExposure,
    scheduleTruncated,
    homogeneousStationaryPoissonProcess: true,
    normalizedObservationBox: true,
    geometryOnlyPointEvents: true,
    atomisticNucleusConstructed: false,
    criticalNucleusAtomCountInferred: false,
    crystallographicPoseAssigned: false,
    heterogeneousSitePreferenceInferred: false,
    gctsSeedChanged: false,
    gctsClockChanged: false,
    candidateSetChanged: false,
    targetUsed: false,
    claimBoundary: "Seeded event times and uniform positions from a stationary homogeneous Poisson point process conditional on one validated CNT rate density and a declared finite observation box. The points are nucleation-event hypotheses, not atomistic critical nuclei, crystallographic poses, heterogeneous site preferences, depletion/impingement dynamics, spatial correlations, incubation transients, or GCTS growth seeds.",
  };
}
