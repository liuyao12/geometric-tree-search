import assert from "node:assert/strict";
import { directionalContactExclusion, directionalDisplacementSupport, directionalPairDisplacementSigma,
  displacementClearanceKey, normalizeDisplacementTensors, rotateDisplacementTensor }
  from "../apps/iqc-growth-live/displacement-envelope.js";

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

const quarterTurn = [0, 0, Math.SQRT1_2, Math.SQRT1_2];
const transported = rotateDisplacementTensor(anisotropic, quarterTurn);
assert.ok(Math.abs(transported[0][0] - .01) < 1e-12);
assert.ok(Math.abs(transported[1][1] - .09) < 1e-12);
assert.ok(Math.abs(transported[2][2] - .04) < 1e-12);
assert.equal(rotateDisplacementTensor(anisotropic, [0, 0, 0, 0]), null,
  "a degenerate pose must fail closed rather than fabricate a covariance frame");

const contactRecord = {
  minimumObserved: 2,
  lowerContact: 2.2,
  meanPositionExclusion: 1.8,
  exclusion: 1.5,
};
assert.equal(directionalContactExclusion(contactRecord, null, null, [1, 0, 0]), 1.5,
  "missing live tensors must reproduce the frozen learned scalar exclusion exactly");
assert.ok(Math.abs(directionalContactExclusion(contactRecord, anisotropic, null, [1, 0, 0]) - 1.496) < 1e-12);
assert.ok(Math.abs(directionalContactExclusion(contactRecord, anisotropic, null, [0, 1, 0]) - 1.672) < 1e-12,
  "the hard contact must respond to the live ellipsoid direction");
assert.ok(Math.abs(directionalContactExclusion(contactRecord, transported, null, [0, 1, 0])
  - directionalContactExclusion(contactRecord, anisotropic, null, [1, 0, 0])) < 1e-12,
"transporting both tensor and pair direction by one proper rotation must leave contact admission invariant");

assert.equal(directionalDisplacementSupport(null, [1, 0, 0], 2), 0);
assert.equal(directionalDisplacementSupport(isotropic, [1, 0, 0], 0), 0);
assert.deepEqual(normalizeDisplacementTensors([isotropic, null], 2, 2), [
  [[.01, 0, 0], [0, .01, 0], [0, 0, .01]], null,
]);
assert.equal(displacementClearanceKey("fitted", 2), "fitted:2");
console.log("directional displacement-envelope regression passed");
