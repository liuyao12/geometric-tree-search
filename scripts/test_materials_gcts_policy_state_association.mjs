import assert from "node:assert/strict";
import { finiteStateContrast } from "../apps/iqc-growth-live/policy-state-association.mjs";

const positive = finiteStateContrast([
  { value: 8, changed: true }, { value: 9, changed: true }, { value: 10, changed: true },
  { value: 1, changed: false }, { value: 2, changed: false }, { value: 3, changed: false },
]);
assert.equal(positive.resolved, true);
assert.equal(positive.changedCount, 3);
assert.equal(positive.stableCount, 3);
assert.equal(positive.changedMean, 9);
assert.equal(positive.stableMean, 2);
assert.equal(positive.difference, 7);
assert.equal(positive.observedRange, 9);
assert.ok(Math.abs(positive.normalizedDifference - 7 / 9) < 1e-12);

const negative = finiteStateContrast([
  { value: 1, changed: true }, { value: 2, changed: true }, { value: 3, changed: true },
  { value: 8, changed: false }, { value: 9, changed: false }, { value: 10, changed: false },
]);
assert.equal(negative.resolved, true);
assert.equal(negative.difference, -7);
assert.ok(Math.abs(negative.normalizedDifference + 7 / 9) < 1e-12);

const unresolved = finiteStateContrast([
  { value: 1, changed: true }, { value: 2, changed: true },
  { value: 4, changed: false }, { value: 5, changed: false }, { value: 6, changed: false },
  { value: Number.NaN, changed: true }, { value: 100, changed: "yes" },
]);
assert.equal(unresolved.resolved, false);
assert.deepEqual(unresolved.supportNeeded, { changed: 1, stable: 0 });
assert.equal(unresolved.sampleCount, 5);

const constant = finiteStateContrast([
  { value: 4, changed: true }, { value: 4, changed: true }, { value: 4, changed: true },
  { value: 4, changed: false }, { value: 4, changed: false }, { value: 4, changed: false },
]);
assert.equal(constant.resolved, true);
assert.equal(constant.observedRange, 0);
assert.equal(constant.normalizedDifference, 0);

assert.throws(() => finiteStateContrast([], { minimumPerGroup: 0 }), /positive integer/);
console.log("policy state-association numeric tests passed");
