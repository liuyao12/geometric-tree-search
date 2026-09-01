import assert from "node:assert/strict";
import { buildConditionalNucleationSchedule }
  from "./conditional-nucleation-scheduler.mjs";

const rate = {
  conditionalSteadyStateHomogeneousCnt: true,
  targetUsed: false,
  intrinsicDimension: 3,
  structureSha256: "a".repeat(64),
  workSha256: "b".repeat(64),
  kineticsRequestSha256: "c".repeat(64),
  parentPhase: "liquid",
  nucleusPhase: "solid",
  temperatureKelvin: 1000,
  logRateDensityPerSi: Math.log(10),
};

const options = { characteristicLengthMetre: 1, exposureSeconds: 1,
  randomSeed: 42, maximumEvents: 64 };
const first = buildConditionalNucleationSchedule(rate, options);
const replay = buildConditionalNucleationSchedule(rate, options);
assert.deepEqual(replay, first);
assert.ok(first.scheduledEventCount > 0);
assert.ok(first.events.every((event) => event.eventTimeSeconds <= 1));
assert.ok(first.events.every((event) => event.normalizedPosition.length === 3
  && event.normalizedPosition.every((coordinate) => coordinate > 0 && coordinate < 1)));
assert.equal(first.atomisticNucleusConstructed, false);
assert.equal(first.gctsSeedChanged, false);
assert.equal(first.targetUsed, false);

const another = buildConditionalNucleationSchedule(rate, { ...options, randomSeed: 43 });
assert.notDeepEqual(another.events, first.events);
const twoDimensional = buildConditionalNucleationSchedule({ ...rate, intrinsicDimension: 2 },
  { characteristicLengthMetre: 1, exposureSeconds: 1, randomSeed: 42, maximumEvents: 64 });
assert.ok(twoDimensional.events.every((event) => event.positionMetre.length === 2));
const capped = buildConditionalNucleationSchedule({ ...rate, logRateDensityPerSi: Math.log(1e6) },
  { characteristicLengthMetre: 1, exposureSeconds: 1, randomSeed: 42, maximumEvents: 2 });
assert.equal(capped.scheduledEventCount, 2);
assert.equal(capped.scheduleTruncated, true);
assert.ok(capped.truncationProbe?.waitingUniform > 0
  && capped.truncationProbe?.waitingUniform < 1);
assert.equal(capped.truncationProbe.fallsInsideExposure, true);
assert.throws(() => buildConditionalNucleationSchedule({ ...rate, targetUsed: true }, options),
  /target-blind/);
assert.throws(() => buildConditionalNucleationSchedule(rate,
  { ...options, maximumEvents: 513 }), /maximum events/);

console.log("conditional nucleation scheduler numerical tests passed");
