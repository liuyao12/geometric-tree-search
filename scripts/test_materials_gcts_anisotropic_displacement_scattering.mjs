import assert from "node:assert/strict";
import { anisotropicDisplacementDampedWeightedPowderStructureFactor,
  displacementDampedWeightedPowderStructureFactor, weightedPowderStructureFactor }
  from "../apps/iqc-growth-live/structure-observables.js";

const options = { qMin: 1, qMax: 9, bins: 17 };
const zeroTensor = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
const zero = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [1, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
], 2, 3, options);
const undamped = weightedPowderStructureFactor([{ distance: 1, weightProduct: 1 }], 2, 3, options);
assert.deepEqual(zero.values, undamped.values,
  "zero displacement covariance must exactly reproduce the mean-position curve");

const isotropicTensor = [[.08, 0, 0], [0, .08, 0], [0, 0, .08]];
const isotropic = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1,
    meanSquareTensor: isotropicTensor.map((row) => row.map((value) => value / 2)) },
  { position: [1, 0, 0], weight: 1,
    meanSquareTensor: isotropicTensor.map((row) => row.map((value) => value / 2)) },
], 2, 3, options);
const ueq = displacementDampedWeightedPowderStructureFactor([
  { distance: 1, weightProduct: 1, meanSquareSum: .08 },
], 2, 3, options);
assert.deepEqual(isotropic.values, ueq.values,
  "isotropic covariance must retain the exact analytic Ueq path");

const parallel = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [1, 0, 0], weight: 1,
    meanSquareTensor: [[.18, 0, 0], [0, .01, 0], [0, 0, .01]] },
], 2, 3, options);
const transverse = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [1, 0, 0], weight: 1,
    meanSquareTensor: [[.01, 0, 0], [0, .18, 0], [0, 0, .01]] },
], 2, 3, options);
assert.notDeepEqual(parallel.values, transverse.values,
  "full Uij treatment must retain covariance orientation relative to pair geometry");

const rotated = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [0, 1, 0], weight: 1,
    meanSquareTensor: [[.01, 0, 0], [0, .18, 0], [0, 0, .01]] },
], 2, 3, options);
parallel.values.forEach((value, index) => assert.ok(Math.abs(value - rotated.values[index]) < 3e-3,
  "rotating the pair and covariance together must preserve the powder curve"));

const angle = .371;
const cosine = Math.cos(angle); const sine = Math.sin(angle);
const rotation = [[cosine, -sine, 0], [sine, cosine, 0], [0, 0, 1]];
const multiply = (first, second) => first.map((row) => second[0].map((_, column) =>
  row.reduce((sum, value, index) => sum + value * second[index][column], 0)));
const transpose = (matrix) => matrix[0].map((_, column) => matrix.map((row) => row[column]));
const rotatedTensor = multiply(multiply(rotation, [[.18, .025, 0], [.025, .04, 0], [0, 0, .01]]),
  transpose(rotation));
const generic = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [1, .25, 0], weight: 1,
    meanSquareTensor: [[.18, .025, 0], [.025, .04, 0], [0, 0, .01]] },
], 2, 3, options);
const genericRotated = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [cosine - .25 * sine, sine + .25 * cosine, 0], weight: 1,
    meanSquareTensor: rotatedTensor },
], 2, 3, options);
generic.values.forEach((value, index) => assert.ok(Math.abs(value - genericRotated.values[index]) < 8e-3,
  "a generic joint proper rotation must preserve the principal-geometry powder curve"));

const planar = anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0], weight: 1, meanSquareTensor: [[0, 0], [0, 0]] },
  { position: [1, .3], weight: 1, meanSquareTensor: [[.12, .02], [.02, .03]] },
], 2, 2, options);
assert.equal(planar.orientationQuadrature, "96-direction circle");
assert.ok(planar.values.every(Number.isFinite));
assert.equal(parallel.orientationQuadrature, "96-direction Fibonacci sphere");
assert.equal(parallel.anisotropicSiteTerms, 1);
assert.equal(parallel.diffuseRedistributionIncluded, false);

assert.throws(() => anisotropicDisplacementDampedWeightedPowderStructureFactor([
  { position: [0, 0, 0], weight: 1, meanSquareTensor: zeroTensor },
  { position: [1, 0, 0], weight: 1,
    meanSquareTensor: [[-.1, 0, 0], [0, 0, 0], [0, 0, 0]] },
], 2, 3, options), /positive-semidefinite/);

console.log("anisotropic reported-displacement powder attenuation regression passed");
