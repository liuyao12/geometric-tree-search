import assert from "node:assert/strict";
import { buildKineticEventSpectrum } from "./kinetic-event-spectrum.mjs";

const spectrum = buildKineticEventSpectrum({
  mode: "seeded-kmc",
  temperatureKelvin: 600,
  selectedCandidateId: "detach-b",
  records: [
    { candidateId: "attach-a", eventDirection: "attach", barrierElectronVolt: .4,
      uncertaintyElectronVolt: .02, attemptFrequencyPerSecond: 1e13,
      attemptFrequencyUncertaintyLog10: .1, log10RatePerSecond: 9,
      log10RateLowerPerSecond: 8.5, log10RateUpperPerSecond: 9.5,
      probabilityWithinFrozenCatalog: .7 },
    { candidateId: "detach-b", eventDirection: "detach", barrierElectronVolt: .5,
      uncertaintyElectronVolt: .03, attemptFrequencyPerSecond: 8e12,
      attemptFrequencyUncertaintyLog10: .15, log10RatePerSecond: 8.2,
      log10RateLowerPerSecond: 7.4, log10RateUpperPerSecond: 9.1,
      probabilityWithinFrozenCatalog: .2 },
    { candidateId: "attach-c", eventDirection: "attach", barrierElectronVolt: .8,
      uncertaintyElectronVolt: .02, attemptFrequencyPerSecond: 2e12,
      attemptFrequencyUncertaintyLog10: .1, log10RatePerSecond: 6,
      log10RateLowerPerSecond: 5.6, log10RateUpperPerSecond: 6.4,
      probabilityWithinFrozenCatalog: .1 },
  ],
});

assert.equal(spectrum.candidateCount, 3);
assert.equal(spectrum.selectedRank, 2);
assert.equal(spectrum.selectedEventDirection, "detach");
assert.ok(Math.abs(spectrum.probabilityMassByDirection.attach - .8) < 1e-12);
assert.ok(Math.abs(spectrum.probabilityMassByDirection.detach - .2) < 1e-12);
assert.equal(spectrum.uncertaintyCompetitiveCandidateCount, 2);
assert.equal(spectrum.fastestCandidateSeparatedByUncertainty, false);
assert.equal(spectrum.selectedInsideFastestUncertaintySet, true);
assert.equal(spectrum.catalogCharacter, "few-event dominated");
assert.equal(spectrum.rateSpanDecades, 3);
assert.ok(spectrum.effectiveCompetingEventCount > 1);
assert.equal(spectrum.targetUsed, false);
assert.equal(spectrum.selectedEventChanged, false);

assert.throws(() => buildKineticEventSpectrum({ temperatureKelvin: 300,
  selectedCandidateId: "a", records: [{ ...spectrum.rankedRecords[0],
    probabilityWithinFrozenCatalog: .9 }] }), /sum to one/);
assert.throws(() => buildKineticEventSpectrum({ temperatureKelvin: 300,
  selectedCandidateId: "missing", records: spectrum.rankedRecords }), /absent/);

console.log("kinetic event-spectrum tests passed");
