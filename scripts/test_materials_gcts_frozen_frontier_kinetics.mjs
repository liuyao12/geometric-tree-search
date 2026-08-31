import assert from "node:assert/strict";
import {
  BOLTZMANN_ELECTRON_VOLT_PER_KELVIN,
  buildFrozenKineticCompetition,
} from "../apps/iqc-growth-live/frozen-frontier-kinetics.mjs";

const records = [
  { candidateId: "slow", eventDirection: "detach", barrierElectronVolt: .8, uncertaintyElectronVolt: .03,
    attemptFrequencyPerSecond: 1e13, attemptFrequencyUncertaintyLog10: .1 },
  { candidateId: "fast", barrierElectronVolt: .4, uncertaintyElectronVolt: .02,
    attemptFrequencyPerSecond: 1e13, attemptFrequencyUncertaintyLog10: .1 },
];

const maximum = buildFrozenKineticCompetition(records, {
  temperatureKelvin: 600, mode: "rate-maximum",
});
assert.equal(maximum.selectedCandidateId, "fast");
assert.equal(maximum.selectedEventDirection, "attach");
assert.equal(maximum.attachmentEventCount, 1);
assert.equal(maximum.detachmentEventCount, 1);
assert.equal(maximum.twoWayEventGeometryPresent, true);
assert.equal(maximum.detailedBalanceCertified, false);
assert.equal(maximum.waitingTimeSeconds, null);
assert.equal(maximum.catalogConditionalClock, false);
assert.ok(maximum.records.find((record) => record.candidateId === "fast").ratePerSecond
  > maximum.records.find((record) => record.candidateId === "slow").ratePerSecond);
assert.ok(Math.abs(maximum.records.reduce((sum, record) =>
  sum + record.probabilityWithinFrozenCatalog, 0) - 1) < 1e-12);
const withExchange = buildFrozenKineticCompetition([...records,
  { candidateId: "exchange", eventDirection: "exchange", barrierElectronVolt: .6,
    uncertaintyElectronVolt: .02, attemptFrequencyPerSecond: 1e13,
    attemptFrequencyUncertaintyLog10: .1 }], { temperatureKelvin: 600 });
assert.equal(withExchange.speciesExchangeEventCount, 1);
assert.equal(withExchange.records.find((record) =>
  record.candidateId === "exchange").eventDirection, "exchange");

const stochastic = buildFrozenKineticCompetition(records, {
  temperatureKelvin: 600, mode: "seeded-kmc", eventUniform: .5, waitingUniform: .25,
});
assert.equal(stochastic.selectedCandidateId, "fast");
assert.ok(stochastic.waitingTimeSeconds > 0);
assert.equal(stochastic.catalogConditionalClock, true);
const reversed = buildFrozenKineticCompetition([...records].reverse(), {
  temperatureKelvin: 600, mode: "seeded-kmc", eventUniform: .5, waitingUniform: .25,
});
assert.equal(reversed.selectedCandidateId, stochastic.selectedCandidateId);
assert.equal(reversed.waitingTimeSeconds, stochastic.waitingTimeSeconds);
const expectedFastLogRate = Math.log(1e13)
  - .4 / (BOLTZMANN_ELECTRON_VOLT_PER_KELVIN * 600);
assert.ok(Math.abs(stochastic.records.find((record) => record.candidateId === "fast").logRatePerSecond
  - expectedFastLogRate) < 1e-12);

assert.throws(() => buildFrozenKineticCompetition(records, { temperatureKelvin: 0 }), /between 1 and 5000/);
assert.throws(() => buildFrozenKineticCompetition([{ ...records[0], attemptFrequencyPerSecond: 0 }],
  { temperatureKelvin: 300 }), /positive/);
assert.throws(() => buildFrozenKineticCompetition([...records, records[0]],
  { temperatureKelvin: 300 }), /unique/);

console.log("frozen frontier kinetics contract: passed");
