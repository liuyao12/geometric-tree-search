import assert from "node:assert/strict";
import {
  SCORE_NORMALIZATION_ALIASES,
  SCORE_NORMALIZATION_SPECS,
  scoreNormalizationAudit,
} from "../apps/iqc-growth-live/score-normalization.mjs";

const expected = [
  "grammar-priority", "known-window-gain", "geometric-strain", "external-calibration",
  "composition", "solute-partition", "formal-charge", "charge-geometry", "charge-moment",
  "ionic-pair", "bond-valence", "surface", "bulk-surface", "attachment", "habit",
  "defect", "coherency", "front", "capillary", "epitaxy", "drive", "thermal",
  "robustness", "microstructure", "loop", "arrival", "exposure", "exploration",
];
assert.deepEqual(Object.keys(SCORE_NORMALIZATION_SPECS), expected);
for (const [alias, canonical] of Object.entries(SCORE_NORMALIZATION_ALIASES)) {
  const audit = scoreNormalizationAudit(alias, { nearestNeighborAngstrom: 2.8, metricToleranceAngstrom: .03 });
  assert.equal(audit.canonicalId, canonical);
}
for (const id of expected) {
  const audit = scoreNormalizationAudit(id, { nearestNeighborAngstrom: 2.8, metricToleranceAngstrom: .03 });
  assert.equal(audit.outputUnit, "dimensionless score coordinate");
  assert.equal(audit.declaredWeightUnit, "dimensionless multiplier");
  assert.equal(audit.candidateGeometryChanged, false);
  assert.equal(audit.hardAdmissionChanged, false);
  assert.equal(audit.physicalTimeModeled, false);
  assert.ok(audit.sourceQuantity && audit.sourceUnit && audit.referenceScale && audit.transform && audit.outputDomain);
}
const strain = scoreNormalizationAudit("geometric-strain", { nearestNeighborAngstrom: 2.8, metricToleranceAngstrom: .03 });
assert.match(strain.sourceUnit, /Å/);
assert.equal(strain.resolvedScales.nearestNeighborAngstrom, 2.8);
assert.equal(strain.resolvedScales.metricToleranceAngstrom, .03);
assert.throws(() => scoreNormalizationAudit("unknown-term"), /missing score normalization specification/);
console.log("score normalization contract passed");
