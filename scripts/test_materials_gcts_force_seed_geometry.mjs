import assert from "node:assert/strict";
import { boundedForceSeedOffset, forceMagnitudeP90, meanForceVectors }
  from "../apps/iqc-growth-live/force-seed-geometry.js";

const sample = [[1, 0, 0], [2, 0, 0], [3, 0, 0], [4, 0, 0], [5, 0, 0],
  [6, 0, 0], [7, 0, 0], [8, 0, 0], [9, 0, 0], [10, 0, 0]];
assert.equal(forceMagnitudeP90(sample), 9);
assert.equal(forceMagnitudeP90([[0, 0, 0]]), null);

const weak = boundedForceSeedOffset([0, 3, 4], 10, .2);
assert.deepEqual(weak, [0, .06, .08]);
assert(Math.abs(Math.hypot(...weak) - .1) < 1e-12);
const capped = boundedForceSeedOffset([0, 30, 40], 10, .2);
assert(Math.abs(Math.hypot(...capped) - .2) < 1e-12);
assert.deepEqual(boundedForceSeedOffset([0, 0, 0], 10, .2), [0, 0, 0]);

const vectors = [[1, 2, 3], [3, 2, 1], [-1, 2, -1]];
const mean = meanForceVectors(vectors);
assert.deepEqual(mean, [1, 2, 1]);
assert.deepEqual(meanForceVectors([...vectors].reverse()), mean,
  "commuting-witness consensus must be order independent");
assert.throws(() => boundedForceSeedOffset([1, 2], 1, .1), /3-vector/);
assert.throws(() => boundedForceSeedOffset([1, 2, 3], 0, .1), /reference scale/);

console.log("bounded residual-force seed geometry: passed");
