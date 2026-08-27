import assert from "node:assert/strict";
import { nomadStressTensorGigaPascal, normalizedStressShapeDeformation, stressTensorSummary }
  from "../apps/iqc-growth-live/stress-geometry.js";

const tensor = nomadStressTensorGigaPascal([
  [2e9, 2e8, 0],
  [4e8, -1e9, 0],
  [0, 0, 1e9],
]);
assert.deepEqual(tensor.map((row) => row.map((value) => Number(value.toFixed(12)))),
  [[2, .3, 0], [.3, -1, 0], [0, 0, 1]]);
const summary = stressTensorSummary(tensor);
assert.ok(Math.abs(summary.hydrostaticGigaPascal - 2 / 3) < 1e-12);
assert.ok(Math.abs(summary.frobeniusGigaPascal - Math.sqrt(6.18)) < 1e-12);
assert.ok(summary.deviatoricFrobeniusGigaPascal > 0);

const follow = normalizedStressShapeDeformation(tensor, .02, 1);
const reverse = normalizedStressShapeDeformation(tensor, .02, -1);
for (let first = 0; first < 3; first++) for (let second = 0; second < 3; second++) {
  const identity = first === second ? 1 : 0;
  assert.ok(Math.abs((follow[first][second] - identity) + (reverse[first][second] - identity)) < 1e-12);
}
assert.equal(nomadStressTensorGigaPascal([[1, 2], [3, 4]]), null);
assert.equal(normalizedStressShapeDeformation([[0, 0, 0], [0, 0, 0], [0, 0, 0]], .02), null);
assert.equal(normalizedStressShapeDeformation(tensor, .2), null);

console.log("stress geometry: passed");
