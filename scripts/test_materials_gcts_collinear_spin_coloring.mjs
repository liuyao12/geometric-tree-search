import assert from "node:assert/strict";
import {
  auditScalarSpinOverlaps,
  scalarSpinCompatible,
  scalarSpinPolarity,
} from "../apps/iqc-growth-live/collinear-spin-coloring.js";

assert.equal(scalarSpinPolarity(2.4), 1);
assert.equal(scalarSpinPolarity(-.1), -1);
assert.equal(scalarSpinPolarity(1e-12), 0);
assert.equal(scalarSpinPolarity(null), null);
assert.equal(scalarSpinCompatible(2, .3), true);
assert.equal(scalarSpinCompatible(-2, -.3), true);
assert.equal(scalarSpinCompatible(2, -.3), false);
assert.equal(scalarSpinCompatible(0, .3), false);
assert.equal(scalarSpinCompatible(null, -.3), true,
  "a missing archive label must remain unconstrained");
assert.equal(scalarSpinCompatible(2, -.3, { enabled: false }), true,
  "the explicit chemistry-only ablation must restore the uncolored overlap");

assert.deepEqual(auditScalarSpinOverlaps([[1, 2], [-1, -.2], [1, -1], [null, 1]]), {
  suppliedPairs: 3,
  compatiblePairs: 2,
  conflictingPairs: 1,
  missingPairs: 1,
  hardColoringApplied: true,
  vectorAxisInferred: false,
  magneticEnergyInferred: false,
});

console.log("collinear scalar-spin coloring regression passed");
