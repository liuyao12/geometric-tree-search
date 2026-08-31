import assert from "node:assert/strict";
import { buildTemperatureProgrammedKinetics, inspectTemperatureProgram }
  from "./temperature-programmed-kinetics.mjs";

const records = [
  { candidateId: "low-barrier", eventDirection: "attach", barrierElectronVolt: .35,
    uncertaintyElectronVolt: .01, attemptFrequencyPerSecond: 1e8,
    attemptFrequencyUncertaintyLog10: .05 },
  { candidateId: "high-prefactor", eventDirection: "hop", barrierElectronVolt: .7,
    uncertaintyElectronVolt: .01, attemptFrequencyPerSecond: 1e14,
    attemptFrequencyUncertaintyLog10: .05 },
  { candidateId: "detach", eventDirection: "detach", barrierElectronVolt: 1.1,
    uncertaintyElectronVolt: .02, attemptFrequencyPerSecond: 1e12,
    attemptFrequencyUncertaintyLog10: .1 },
];

const withheld = buildTemperatureProgrammedKinetics(records, { scope: "single-temperature" });
assert.equal(withheld.available, false);
assert.equal(withheld.constantHtstRangeEvaluationPerformed, false);
assert.equal(withheld.unauthorizedTemperatureExtrapolationPerformed, false);

const program = buildTemperatureProgrammedKinetics(records, {
  scope: "bounded-constant-htst", minimumKelvin: 150, maximumKelvin: 1500,
  externallyAuthorized: true, barrierAndPrefactorAssumedConstant: true,
}, { sampleCount: 61 });
assert.equal(program.available, true);
assert.equal(program.samples.length, 61);
assert.equal(program.samples[0].temperatureKelvin, 150);
assert.ok(Math.abs(program.samples.at(-1).temperatureKelvin - 1500) < 1e-9);
assert.equal(program.samples[0].fastestCandidateId, "low-barrier");
assert.equal(program.samples.at(-1).fastestCandidateId, "high-prefactor");
assert.ok(program.eventCrossovers.some((entry) => entry.from === "low-barrier"
  && entry.to === "high-prefactor"));
assert.ok(program.directionCrossovers.some((entry) => entry.from === "attach"
  && entry.to === "hop"));
assert.equal(program.candidateSetChanged, false);
assert.equal(program.targetUsed, false);
assert.equal(program.missingEventsInferred, false);
assert.equal(program.constantHtstRangeEvaluationPerformed, true);
assert.equal(program.unauthorizedTemperatureExtrapolationPerformed, false);
const inspected = inspectTemperatureProgram(program, 700);
assert.ok(inspected.temperatureKelvin >= 150 && inspected.temperatureKelvin <= 1500);
assert.equal(inspectTemperatureProgram(withheld, 700), null);
assert.equal(buildTemperatureProgrammedKinetics(records, {
  scope: "bounded-constant-htst", minimumKelvin: 150, maximumKelvin: 1500,
  externallyAuthorized: false, barrierAndPrefactorAssumedConstant: true,
}, { sampleCount: 3 }).available, false); // unavailable declarations abstain before sampling

console.log("temperature-programmed finite-catalog kinetics: ok");
