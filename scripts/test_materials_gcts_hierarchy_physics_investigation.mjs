import assert from "node:assert/strict";
import { buildHierarchyPhysicsInvestigation, hierarchyPhysicsInvestigationPrograms }
  from "../apps/iqc-growth-live/hierarchy-physics-investigation.mjs";

assert.deepEqual(hierarchyPhysicsInvestigationPrograms(), [
  "colored-geometry", "proper-pose", "connection-topology", "steric-exclusion",
  "composition", "residuals", "local-response", "interface", "kinetics", "nonlocal",
]);

for (const receipt of ["iqc-reencoding", "iqc-compression", "cdyb-transfer", "nacl-stationary"]) {
  for (const channel of hierarchyPhysicsInvestigationPrograms()) {
    for (const stage of ["atomic", "cluster", "macro", "stationary"]) {
      const plan = buildHierarchyPhysicsInvestigation(receipt, channel, stage);
      assert.equal(plan.schema, "gcts-hierarchy-physics-investigation-v1");
      assert.equal(plan.receiptId, receipt);
      assert.equal(plan.channelId, channel);
      assert.equal(plan.stageId, stage);
      assert.ok(["exact", "reevaluated", "representation", "open"].includes(plan.status));
      assert.ok(plan.question.length > 30);
      assert.ok(plan.evidence.length > 40);
      assert.ok(plan.encoding.length > 40);
      assert.ok(plan.validation.length > 40);
      assert.ok(plan.execution.length > 40);
      assert.ok(plan.greenGate.length > 40);
      assert.ok([0, 1, 3, 4].includes(plan.route.stage));
      assert.ok(plan.route.scenario);
      assert.ok(plan.route.focusId);
      assert.equal(plan.candidateGeometryFrozenDuringAblation, true);
      assert.equal(plan.targetUsedForFitOrSelection, false);
      assert.equal(plan.claimAllowed, plan.status === "exact" || plan.status === "reevaluated");
    }
  }
}

const iqcResidual = buildHierarchyPhysicsInvestigation("iqc-reencoding", "residuals", "macro");
assert.equal(iqcResidual.status, "representation");
assert.equal(iqcResidual.claimAllowed, false);
assert.equal(iqcResidual.route.stage, 1);
assert.match(iqcResidual.execution, /never emit novel sites/);
assert.match(iqcResidual.greenGate, /literal coordinates never enter a generative rule/);

const iqcKinetics = buildHierarchyPhysicsInvestigation("iqc-reencoding", "kinetics", "stationary");
assert.equal(iqcKinetics.status, "open");
assert.equal(iqcKinetics.externalEvidenceRequired, true);
assert.equal(iqcKinetics.physicalTimeClaimed, false);
assert.equal(iqcKinetics.route.stage, 4);
assert.match(iqcKinetics.greenGate, /chronology or first-passage/);

const naclGeometry = buildHierarchyPhysicsInvestigation("nacl-stationary", "colored-geometry", "stationary");
assert.equal(naclGeometry.status, "exact");
assert.equal(naclGeometry.claimAllowed, true);
assert.equal(naclGeometry.route.scenario, "competition");
assert.match(naclGeometry.nextAction, /independent spatial\/material holdout/);

const cdybTopology = buildHierarchyPhysicsInvestigation("cdyb-transfer", "connection-topology", "stationary");
assert.equal(cdybTopology.status, "open");
assert.equal(cdybTopology.claimAllowed, false);
assert.match(cdybTopology.claimBoundary, /No status is upgraded merely because the hierarchy is deep/);

assert.throws(() => buildHierarchyPhysicsInvestigation("iqc-reencoding", "missing", "macro"),
  /Unknown hierarchy physics channel/);
assert.throws(() => buildHierarchyPhysicsInvestigation("iqc-reencoding", "kinetics", "century"),
  /Unknown hierarchy transport stage/);

console.log("hierarchy physics investigation model passed");
