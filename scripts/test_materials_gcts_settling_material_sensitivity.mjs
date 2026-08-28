import assert from "node:assert/strict";
import {
  SETTLING_MATERIAL_FIELDS,
  compareSettlingMaterialFingerprints,
} from "../apps/iqc-growth-live/settling-material-sensitivity.mjs";

const baseline = {
  atomCount: 10, chemistryDigest: "A6B4", phenotype: "compact-3D", intrinsicDimension: 3,
  coordinationDeficit: .2, packingDensity: .9, localOrder: .4, centrosymmetry: .15,
  peakProminence: 1.2, radiusOfGyrationAngstrom: 4, maximumExtentAngstrom: 9,
  relativeShapeAnisotropy: .1,
};
const projected = { ...baseline, coordinationDeficit: .17, localOrder: .45,
  radiusOfGyrationAngstrom: 3.98 };
const comparison = compareSettlingMaterialFingerprints(baseline, projected);
assert.deepEqual(comparison.changedFields,
  ["coordinationDeficit", "localOrder", "radiusOfGyrationAngstrom"]);
assert.equal(comparison.deltas.coordinationDeficit, -.03);
assert.equal(comparison.atomCountInvariant, true);
assert.equal(comparison.chemistryInvariant, true);
assert.equal(comparison.targetUsed, false);
assert.equal(comparison.usedForRanking, false);
assert.equal(SETTLING_MATERIAL_FIELDS.length, 8);

const unchanged = compareSettlingMaterialFingerprints(baseline, { ...baseline });
assert.equal(unchanged.changedFieldCount, 0);

const categorical = compareSettlingMaterialFingerprints(baseline,
  { ...baseline, phenotype: "planar", intrinsicDimension: 2 });
assert.deepEqual(categorical.changedFields, ["phenotype", "intrinsicDimension"]);

console.log("settling material sensitivity contract passed");
