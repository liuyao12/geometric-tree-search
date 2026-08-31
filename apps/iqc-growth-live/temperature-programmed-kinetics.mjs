import { buildFrozenKineticCompetition }
  from "./frozen-frontier-kinetics.mjs?v=20260831-385";

export const TEMPERATURE_PROGRAM_SAMPLE_COUNT = 41;
export const TEMPERATURE_PROGRAM_DIRECTIONS = Object.freeze([
  "attach", "detach", "hop", "exchange",
]);

const finite = (value) => Number.isFinite(Number(value));

function boundedApplicability(applicability) {
  if (applicability?.scope !== "bounded-constant-htst"
      || applicability.externallyAuthorized !== true
      || applicability.barrierAndPrefactorAssumedConstant !== true
      || !finite(applicability.minimumKelvin) || !finite(applicability.maximumKelvin)) return null;
  const minimumKelvin = Number(applicability.minimumKelvin);
  const maximumKelvin = Number(applicability.maximumKelvin);
  if (minimumKelvin < 1 || maximumKelvin > 5000 || minimumKelvin >= maximumKelvin) return null;
  return { scope: applicability.scope, minimumKelvin, maximumKelvin,
    externallyAuthorized: true, barrierAndPrefactorAssumedConstant: true };
}

function temperatureGrid(minimumKelvin, maximumKelvin, sampleCount) {
  // Uniform inverse-temperature sampling makes straight Arrhenius trends equally legible.
  const coldInverse = 1000 / minimumKelvin;
  const hotInverse = 1000 / maximumKelvin;
  return Array.from({ length: sampleCount }, (_, index) => {
    const fraction = index / (sampleCount - 1);
    const inverseTemperaturePerKilokelvin = coldInverse
      + (hotInverse - coldInverse) * fraction;
    return {
      temperatureKelvin: 1000 / inverseTemperaturePerKilokelvin,
      inverseTemperaturePerKilokelvin,
    };
  });
}

function directionMass(records, direction) {
  return records.filter((record) => record.eventDirection === direction)
    .reduce((sum, record) => sum + record.probabilityWithinFrozenCatalog, 0);
}

function maximumDirectionRecord(records, direction) {
  return records.filter((record) => record.eventDirection === direction)
    .sort((first, second) => second.log10RatePerSecond - first.log10RatePerSecond
      || first.candidateId.localeCompare(second.candidateId))[0] || null;
}

function effectiveCount(records) {
  const entropy = -records.reduce((sum, record) => {
    const probability = record.probabilityWithinFrozenCatalog;
    return sum + (probability > 0 ? probability * Math.log(probability) : 0);
  }, 0);
  return Math.exp(entropy);
}

function uncertaintySeparated(fastest, records) {
  return records.every((record) => record.candidateId === fastest.candidateId
    || fastest.log10RateLowerPerSecond > record.log10RateUpperPerSecond);
}

function transitionIntervals(samples, field) {
  const intervals = [];
  for (let index = 1; index < samples.length; index += 1) {
    if (samples[index - 1][field] === samples[index][field]) continue;
    intervals.push({
      from: samples[index - 1][field],
      to: samples[index][field],
      lowerKelvin: Math.min(samples[index - 1].temperatureKelvin,
        samples[index].temperatureKelvin),
      upperKelvin: Math.max(samples[index - 1].temperatureKelvin,
        samples[index].temperatureKelvin),
    });
  }
  return intervals;
}

export function buildTemperatureProgrammedKinetics(records, applicability, {
  sampleCount = TEMPERATURE_PROGRAM_SAMPLE_COUNT,
} = {}) {
  const bounded = boundedApplicability(applicability);
  if (!bounded) {
    return {
      schema: 1,
      available: false,
      reason: "A bounded-constant-htst temperature applicability declaration, external authorization, and explicit constant barrier/prefactor assumption are required.",
      candidateSetChanged: false,
      targetUsed: false,
      constantHtstRangeEvaluationPerformed: false,
      unauthorizedTemperatureExtrapolationPerformed: false,
      claimBoundary: "No temperature sweep is inferred from a single-temperature or undeclared HTST response.",
    };
  }
  const count = Math.trunc(Number(sampleCount));
  if (!Number.isInteger(count) || count < 5 || count > 401) {
    throw new RangeError("sampleCount must be an integer between 5 and 401");
  }
  const samples = temperatureGrid(bounded.minimumKelvin, bounded.maximumKelvin, count)
    .map(({ temperatureKelvin, inverseTemperaturePerKilokelvin }) => {
      const competition = buildFrozenKineticCompetition(records,
        { temperatureKelvin, mode: "rate-maximum" });
      const fastest = competition.records.find((record) =>
        record.candidateId === competition.selectedCandidateId);
      const directionProbabilityMass = Object.fromEntries(TEMPERATURE_PROGRAM_DIRECTIONS
        .map((direction) => [direction, directionMass(competition.records, direction)]));
      const leadingDirection = [...TEMPERATURE_PROGRAM_DIRECTIONS]
        .sort((first, second) => directionProbabilityMass[second]
          - directionProbabilityMass[first] || first.localeCompare(second))[0];
      const maximumLog10RateByDirection = Object.fromEntries(TEMPERATURE_PROGRAM_DIRECTIONS
        .map((direction) => [direction,
          maximumDirectionRecord(competition.records, direction)?.log10RatePerSecond ?? null]));
      return {
        temperatureKelvin,
        inverseTemperaturePerKilokelvin,
        fastestCandidateId: fastest.candidateId,
        fastestEventDirection: fastest.eventDirection,
        fastestLog10RatePerSecond: fastest.log10RatePerSecond,
        fastestProbabilityWithinFrozenCatalog: fastest.probabilityWithinFrozenCatalog,
        fastestSeparatedByUncertainty: uncertaintySeparated(fastest, competition.records),
        leadingDirection,
        directionProbabilityMass,
        maximumLog10RateByDirection,
        log10TotalRatePerSecond: competition.log10TotalRatePerSecond,
        effectiveCompetingEventCount: effectiveCount(competition.records),
      };
    });
  const eventCrossovers = transitionIntervals(samples, "fastestCandidateId");
  const directionCrossovers = transitionIntervals(samples, "leadingDirection");
  return {
    schema: 1,
    available: true,
    model: "externally-authorized bounded constant-HTST finite-catalog sweep",
    applicability: bounded,
    sampleCount: samples.length,
    candidateCount: records.length,
    samples,
    eventCrossovers,
    directionCrossovers,
    uncertaintySeparatedSampleCount: samples.filter((sample) =>
      sample.fastestSeparatedByUncertainty).length,
    candidateSetChanged: false,
    targetUsed: false,
    constantHtstRangeEvaluationPerformed: true,
    unauthorizedTemperatureExtrapolationPerformed: false,
    missingEventsInferred: false,
    claimBoundary: "This map re-evaluates one unchanged, finite hard-admitted event catalog only over the externally authorized temperature interval, under the explicit assumption that supplied harmonic barriers and prefactors remain constant. It does not discover missing mechanisms, temperature-dependent free energies, anharmonicity, phase changes, recrossing, or a complete growth law.",
  };
}

export function inspectTemperatureProgram(program, temperatureKelvin) {
  if (!program?.available || !Array.isArray(program.samples) || !program.samples.length) return null;
  if (!finite(temperatureKelvin)) throw new TypeError("temperatureKelvin must be finite");
  const bounded = Math.max(program.applicability.minimumKelvin,
    Math.min(program.applicability.maximumKelvin, Number(temperatureKelvin)));
  return [...program.samples].sort((first, second) =>
    Math.abs(first.temperatureKelvin - bounded) - Math.abs(second.temperatureKelvin - bounded))[0];
}
