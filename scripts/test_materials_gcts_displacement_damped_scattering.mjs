import assert from "node:assert/strict";
import { displacementDampedWeightedPowderStructureFactor, weightedPowderStructureFactor }
  from "../apps/iqc-growth-live/structure-observables.js";

const basePairs = [{ distance: 1, weightProduct: 1 }];
const undamped = weightedPowderStructureFactor(basePairs, 2, 3, { qMin: 2, qMax: 10, bins: 5 });
const zero = displacementDampedWeightedPowderStructureFactor(
  [{ ...basePairs[0], meanSquareSum: 0 }], 2, 3, { qMin: 2, qMax: 10, bins: 5 });
assert.deepEqual(zero.values, undamped.values, "zero Ueq must reproduce the mean-position curve exactly");

const damped = displacementDampedWeightedPowderStructureFactor(
  [{ ...basePairs[0], meanSquareSum: .04 }], 2, 3, { qMin: 2, qMax: 10, bins: 5 });
assert.equal(damped.coherentDisplacementAttenuation, true);
assert.equal(damped.diffuseRedistributionIncluded, false);
assert.ok(damped.values.every((value, index) => Math.abs(value - 1) <= Math.abs(undamped.values[index] - 1) + 1e-12),
  "reported displacement must attenuate every coherent pair deviation toward the self baseline");
assert.ok(Math.abs(damped.values.at(-1) - 1) < Math.abs(undamped.values.at(-1) - 1));

assert.throws(() => displacementDampedWeightedPowderStructureFactor(
  [{ distance: 1, weightProduct: 1, meanSquareSum: -1 }], 2));
console.log("reported-displacement powder attenuation regression passed");
