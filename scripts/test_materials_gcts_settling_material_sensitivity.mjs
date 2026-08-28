import assert from "node:assert/strict";
import {
  SETTLING_MATERIAL_FIELDS,
  buildSettlingMaterialResponseMatrix,
  buildSettlingMaterialResponseHistory,
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

const arm = (mode, accepted, fingerprint) => ({ mode, attempted: mode !== "off", accepted,
  materialConsequence: compareSettlingMaterialFingerprints(baseline, fingerprint) });
const matrix = buildSettlingMaterialResponseMatrix([
  arm("off", false, baseline),
  arm("gentle", true, { ...baseline, coordinationDeficit: .19, localOrder: .42 }),
  arm("balanced", true, { ...baseline, coordinationDeficit: .18, localOrder: .39 }),
  arm("strong", true, { ...baseline, coordinationDeficit: .17, localOrder: .46,
    phenotype: "elongated-3D" }),
]);
assert.deepEqual(matrix.acceptedModes, ["gentle", "balanced", "strong"]);
assert.equal(matrix.gatePattern, "all-projected-arms-certified");
assert.equal(matrix.rows.find((row) => row.id === "coordinationDeficit").trend,
  "monotone-with-allowance");
assert.equal(matrix.rows.find((row) => row.id === "localOrder").trend,
  "direction-changing");
assert.equal(matrix.rows.find((row) => row.id === "phenotype").trend,
  "threshold-categorical-shift");
assert.equal(matrix.rows.find((row) => row.id === "packingDensity").trend,
  "invariant-across-certified");
assert.equal(matrix.normalization,
  "within-field maximum absolute delta only; no cross-unit scalar");

const inactive = buildSettlingMaterialResponseMatrix([
  arm("off", false, baseline), arm("gentle", false, baseline), arm("strong", false, baseline),
]);
assert.equal(inactive.gatePattern, "no-projected-arm-certified");
assert.equal(inactive.sensitiveFieldCount, 0);

const leap = (index, arms) => ({ index, status: "accepted",
  settlingSensitivity: { arms, selectedMode: "balanced", selectedExecutionMatchesPreview: true,
    materialResponseMatrix: buildSettlingMaterialResponseMatrix(arms) } });
const history = buildSettlingMaterialResponseHistory([
  leap(1, [arm("off", false, baseline),
    arm("gentle", true, { ...baseline, coordinationDeficit: .19 }),
    arm("balanced", true, { ...baseline, coordinationDeficit: .18 }),
    arm("strong", true, { ...baseline, coordinationDeficit: .17 })]),
  leap(2, [arm("off", false, baseline),
    arm("gentle", true, { ...baseline, coordinationDeficit: .21 }),
    arm("balanced", true, { ...baseline, coordinationDeficit: .22 }),
    arm("strong", true, { ...baseline, coordinationDeficit: .23, phenotype: "planar" })]),
  leap(3, [arm("off", false, baseline), arm("gentle", false, baseline),
    arm("balanced", false, baseline), arm("strong", false, baseline)]),
]);
assert.equal(history.retainedLeapCount, 3);
assert.deepEqual(history.retainedLeapIndices, [1, 2, 3]);
assert.equal(history.fields.find((field) => field.id === "coordinationDeficit").pattern,
  "direction-reversing-across-leaps");
assert.equal(history.fields.find((field) => field.id === "coordinationDeficit").compatibleLeapCount, 2);
assert.equal(history.fields.find((field) => field.id === "phenotype").pattern,
  "intermittent-categorical-shift");
assert.equal(history.fields.find((field) => field.id === "packingDensity").pattern,
  "robust-invariant");
assert.equal(history.normalization,
  "within one material field across retained leaps and certified arms only; no cross-unit scalar");
assert.equal(history.physicalTimeModeled, false);

const noCompatibleHistory = buildSettlingMaterialResponseHistory([leap(1, [
  arm("off", false, baseline), arm("gentle", false, baseline),
])]);
assert.equal(noCompatibleHistory.fields[0].pattern, "no-compatible-projections");

console.log("settling material sensitivity contract passed");
