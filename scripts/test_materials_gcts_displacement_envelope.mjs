import assert from "node:assert/strict";
import { directionalDisplacementSupport, directionalPairDisplacementSigma, displacementClearanceKey,
  normalizeDisplacementTensors } from "../apps/iqc-growth-live/displacement-envelope.js";

const isotropic = [[.04, 0, 0], [0, .04, 0], [0, 0, .04]];
assert.ok(Math.abs(directionalDisplacementSupport(isotropic, [1, 2, 3], 2) - .4) < 1e-12);
const anisotropic = [[.09, 0, 0], [0, .01, 0], [0, 0, .04]];
assert.ok(Math.abs(directionalDisplacementSupport(anisotropic, [1, 0, 0], 1) - .3) < 1e-12);
assert.ok(Math.abs(directionalDisplacementSupport(anisotropic, [0, 1, 0], 1) - .1) < 1e-12);
assert.ok(Math.abs(directionalDisplacementSupport(anisotropic, [0, 0, 1], 3) - .6) < 1e-12);
assert.ok(Math.abs(directionalPairDisplacementSigma(anisotropic, isotropic, [1, 0, 0])
  - Math.sqrt(.13)) < 1e-12);
assert.ok(Math.abs(directionalPairDisplacementSigma(anisotropic, isotropic, [0, 1, 0])
  - Math.sqrt(.05)) < 1e-12);
assert.ok(Math.abs(directionalPairDisplacementSigma(anisotropic, null, [1, 0, 0]) - .3) < 1e-12,
  "a missing reported tensor must contribute explicit zero covariance");

const rotation = [[0, -1, 0], [1, 0, 0], [0, 0, 1]];
const matmul = (first, second) => first.map((row) => second[0].map((_, column) =>
  row.reduce((sum, value, index) => sum + value * second[index][column], 0)));
const transpose = (matrix) => matrix[0].map((_, column) => matrix.map((row) => row[column]));
const rotatedTensor = matmul(matmul(rotation, anisotropic), transpose(rotation));
const rotatedDirection = rotation.map((row) => row.reduce((sum, value, index) => sum + value * [1, 2, 3][index], 0));
assert.ok(Math.abs(directionalDisplacementSupport(rotatedTensor, rotatedDirection, 2)
  - directionalDisplacementSupport(anisotropic, [1, 2, 3], 2)) < 1e-12,
"the directional ellipsoid support must be proper-rotation invariant");
const rotatedIsotropic = matmul(matmul(rotation, isotropic), transpose(rotation));
assert.ok(Math.abs(directionalPairDisplacementSigma(rotatedTensor, rotatedIsotropic, rotatedDirection)
  - directionalPairDisplacementSigma(anisotropic, isotropic, [1, 2, 3])) < 1e-12,
"the pair-direction covariance must be proper-rotation invariant");

assert.equal(directionalDisplacementSupport(null, [1, 0, 0], 2), 0);
assert.equal(directionalDisplacementSupport(isotropic, [1, 0, 0], 0), 0);
assert.deepEqual(normalizeDisplacementTensors([isotropic, null], 2, 2), [
  [[.01, 0, 0], [0, .01, 0], [0, 0, .01]], null,
]);
assert.equal(displacementClearanceKey("fitted", 2), "fitted:2");
console.log("directional displacement-envelope regression passed");
