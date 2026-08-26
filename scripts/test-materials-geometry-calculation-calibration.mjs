import assert from "node:assert/strict";
import { geometryCalculationCalibration, geometryCalculationSurrogate, geometryReferenceIndices }
  from "../apps/iqc-growth-live/geometry-calculation-calibration.js";

const monotone = [
  { mismatch: 0, energy: 0, force: 0 },
  { mismatch: 1, energy: 2, force: 4 },
  { mismatch: 2, energy: 4, force: 1 },
  { mismatch: 3, energy: 6, force: 3 },
];
const energy = geometryCalculationCalibration(monotone, "mismatch", "energy");
assert.equal(energy.pairedFrames, 4);
assert.ok(Math.abs(energy.pearson - 1) < 1e-12);
assert.ok(Math.abs(energy.spearman - 1) < 1e-12);
assert.ok(Math.abs(energy.slope - 2) < 1e-12);
assert.ok(Math.abs(energy.intercept) < 1e-12);
assert.equal(energy.predictiveValidationPerformed, false);

const force = geometryCalculationCalibration(monotone, "mismatch", "force");
assert.ok(force.spearman > 0 && force.spearman < 1,
  "rank correlation must distinguish nonmonotone residual force from energy");
const ties = geometryCalculationCalibration([
  { x: 1, y: 2 }, { x: 1, y: 2 }, { x: 2, y: 3 }, { x: 3, y: 4 },
], "x", "y");
assert.ok(Math.abs(ties.spearman - 1) < 1e-12, "average ranks must preserve tied monotonic order");
const missing = geometryCalculationCalibration([{ x: 1, y: null }, { x: 2, y: 3 }], "x", "y");
assert.equal(missing.pairedFrames, 1);
assert.equal(missing.pearson, null);
assert.equal(missing.spearman, null);

assert.deepEqual(geometryReferenceIndices(4, "final"), [3]);
assert.deepEqual(geometryReferenceIndices(4, "first"), [0]);
assert.deepEqual(geometryReferenceIndices(4, "pooled"), [0, 1, 2, 3]);
assert.deepEqual(geometryReferenceIndices(4, "unknown"), [3]);
assert.throws(() => geometryReferenceIndices(0, "pooled"), /requires frames/);

const surrogateRecords = Array.from({ length: 8 }, (_, index) => ({
  distance: index,
  angle: (index % 3) - 1,
  coordination: index % 2,
  energy: 2 * index - .5 * ((index % 3) - 1) + .25 * (index % 2),
}));
const surrogate = geometryCalculationSurrogate(surrogateRecords,
  ["distance", "angle", "coordination"], "energy", { ridge: 1e-6 });
assert.equal(surrogate.available, true);
assert.equal(surrogate.predictions.length, 8);
assert.ok(surrogate.predictionSpearman > .99);
assert.ok(surrogate.meanAbsoluteError < 1e-3);
assert.equal(surrogate.independentValidationClaimed, false);
assert.equal(surrogate.usedForGrowth, false);
const shortSurrogate = geometryCalculationSurrogate(surrogateRecords.slice(0, 4),
  ["distance", "angle", "coordination"], "energy");
assert.equal(shortSurrogate.available, false);
assert.equal(shortSurrogate.requiredPairs, 5);

console.log("geometry/calculation calibration statistics: passed");
