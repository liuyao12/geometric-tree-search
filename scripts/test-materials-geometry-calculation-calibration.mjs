import assert from "node:assert/strict";
import { geometryCalculationCalibration }
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

console.log("geometry/calculation calibration statistics: passed");
