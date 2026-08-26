import assert from "node:assert/strict";
import { applyHypothesisSeparationMultipliers, hypothesisSeparationMultiplier,
  validateHypothesisSeparationExperiment }
  from "../apps/iqc-growth-live/hypothesis-separation.js";

const experiment = {
  schema: 1, arm: "baseline", mode: "conditional",
  pair: { firstId: "charge", secondId: "composition" },
  ablatedTermId: "charge", retainedComparisonTermId: "composition",
  sourceCandidateSetDigest: "candidate-set", sourceAuditDigest: "audit",
  targetUsed: false, coordinatesEmbedded: false, candidateRowsEmbedded: false,
};
assert.equal(validateHypothesisSeparationExperiment(experiment), true);
assert.equal(hypothesisSeparationMultiplier(experiment, "charge"), 1);
const terms = [{ id: "charge", weight: -.25, contribution: -.5 },
  { id: "composition", weight: -.35, contribution: -.2 }];
const baseline = applyHypothesisSeparationMultipliers(terms, experiment);
assert.deepEqual(baseline, terms);
assert.notEqual(baseline[0], terms[0]);
const ablation = applyHypothesisSeparationMultipliers(terms, { ...experiment, arm: "ablation" });
assert.equal(ablation[0].weight, 0);
assert.equal(ablation[0].contribution, 0);
assert.equal(ablation[0].experimentMultiplier, 0);
assert.equal(ablation[1].weight, terms[1].weight);
assert.equal(ablation[1].contribution, terms[1].contribution);
assert.deepEqual(terms, [{ id: "charge", weight: -.25, contribution: -.5 },
  { id: "composition", weight: -.35, contribution: -.2 }]);
assert.equal(validateHypothesisSeparationExperiment({ ...experiment, targetUsed: true }), false);
assert.equal(hypothesisSeparationMultiplier({ ...experiment, pair: { firstId: "charge", secondId: "charge" } }, "charge"), 1);
assert.throws(() => applyHypothesisSeparationMultipliers(null, experiment), /array/);
console.log("materials hypothesis separation: passed");
