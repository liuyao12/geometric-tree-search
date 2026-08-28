import assert from "node:assert/strict";
import { compareShadowMaterialFingerprints, SHADOW_MATERIAL_CONSEQUENCE_FIELDS }
  from "../apps/iqc-growth-live/shadow-material-consequence.mjs";

const baseline = { atomCount: 120, phenotype: "compact", intrinsicDimension: 3,
  radiusOfGyrationAngstrom: 8, maximumExtentAngstrom: 12,
  relativeShapeAnisotropy: .1, compositionDrift: .02, surfaceIntegrity: .3 };
const omitted = { atomCount: 116, phenotype: "elongated", intrinsicDimension: 3,
  radiusOfGyrationAngstrom: 8.5, maximumExtentAngstrom: 13,
  relativeShapeAnisotropy: .25, compositionDrift: .04, surfaceIntegrity: .1 };
const comparison = compareShadowMaterialFingerprints(baseline, omitted);

assert.equal(SHADOW_MATERIAL_CONSEQUENCE_FIELDS.length, 6);
assert.equal(comparison.phenotypeChanged, true);
assert.equal(comparison.intrinsicDimensionChanged, false);
assert.equal(comparison.deltas.atomCount, -4);
assert.equal(comparison.deltas.radiusOfGyrationAngstrom, .5);
assert.ok(Math.abs(comparison.deltas.relativeShapeAnisotropy - .15) < 1e-12);
assert.ok(Math.abs(comparison.deltas.surfaceIntegrity + .2) < 1e-12);
assert.equal(comparison.coordinatesEmbedded, false);
assert.equal(comparison.targetUsed, false);
assert.equal(comparison.executed, false);
assert.equal(comparison.usedForRanking, false);
assert.equal(comparison.causalEffectIdentified, false);

assert.throws(() => compareShadowMaterialFingerprints(null, omitted), /requires two fingerprints/);
console.log("shadow material-consequence contract: pass");
