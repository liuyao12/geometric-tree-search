import assert from "node:assert/strict";
import { buildHierarchyPhysicsProtocolPacket }
  from "../apps/iqc-growth-live/hierarchy-physics-protocol-packet.mjs";
import { bindHierarchyPhysicsProtocolToExecution,
  hierarchyPhysicsProtocolLaunchAuditFromPacket }
  from "../apps/iqc-growth-live/hierarchy-physics-execution-binding.mjs";
import { buildHierarchyPhysicsProtocolConformance,
  hierarchyPhysicsProtocolConformanceChannels,
  hierarchyPhysicsProtocolConformanceRequirements }
  from "../apps/iqc-growth-live/hierarchy-physics-protocol-conformance.mjs";

const packet = await buildHierarchyPhysicsProtocolPacket("iqc-reencoding", "kinetics", "stationary");
const launch = hierarchyPhysicsProtocolLaunchAuditFromPacket({ ...packet.selection,
  expectedSha256: packet.sha256 }, packet);
const binding = bindHierarchyPhysicsProtocolToExecution(launch,
  { scenarioId: "iqc", pipelineStage: 4, receiptBuildId: "20260831-397" });
const requirements = hierarchyPhysicsProtocolConformanceRequirements("kinetics", "stationary");
assert.ok(requirements.some((requirement) => requirement.id === "externalTransitionEvidence"));
assert.ok(requirements.some((requirement) => requirement.id === "threeLevelStationaryWitness"));
assert.equal(new Set(requirements.map((requirement) => requirement.id)).size, requirements.length);

const partialFacts = Object.fromEntries(requirements.map((requirement) => [requirement.id,
  ["protocolFrozenBeforeEvidenceUse", "candidateGeometryFrozen", "targetFreeFitAndSelection"].includes(requirement.id)]));
const partial = buildHierarchyPhysicsProtocolConformance(binding, { facts: partialFacts });
assert.equal(partial.status, "evidence-incomplete");
assert.equal(partial.metRequirements, 3);
assert.ok(partial.totalRequirements > partial.metRequirements);
assert.equal(partial.gateEvaluated, false);
assert.equal(partial.claimUpgradeAllowed, false);
assert.equal(partial.physicalTimeClaimed, false);
assert.equal(partial.targetUsedForFitOrSelection, false);

const allFacts = Object.fromEntries(requirements.map((requirement) => [requirement.id, true]));
const ready = buildHierarchyPhysicsProtocolConformance(binding, { facts: allFacts });
assert.equal(ready.status, "ready-for-sealed-gate");
assert.equal(ready.allRequirementsMet, true);
assert.equal(ready.gateEvaluated, false);
assert.equal(ready.claimUpgradeAllowed, false);

const gateReceiptSha256 = "a".repeat(64);
const passed = buildHierarchyPhysicsProtocolConformance(binding, { facts: allFacts,
  gateEvaluation: { preregistered: true, metricDenominatorsFrozen: true,
    passed: true, receiptSha256: gateReceiptSha256 } });
assert.equal(passed.status, "sealed-gate-passed");
assert.equal(passed.claimUpgradeAllowed, true);
assert.equal(passed.physicalTimeClaimed, true);
assert.equal(passed.gateReceiptSha256, gateReceiptSha256);

const failed = buildHierarchyPhysicsProtocolConformance(binding, { facts: allFacts,
  gateEvaluation: { preregistered: true, metricDenominatorsFrozen: true,
    passed: false, receiptSha256: "b".repeat(64) } });
assert.equal(failed.status, "sealed-gate-failed");
assert.equal(failed.claimUpgradeAllowed, false);
assert.throws(() => buildHierarchyPhysicsProtocolConformance(binding, { facts: allFacts,
  gateEvaluation: { preregistered: false, metricDenominatorsFrozen: true,
    passed: true, receiptSha256: gateReceiptSha256 } }), /gate evaluation/);

const wrongMaterial = bindHierarchyPhysicsProtocolToExecution(launch,
  { scenarioId: "competition", pipelineStage: 4 });
assert.equal(buildHierarchyPhysicsProtocolConformance(wrongMaterial,
  { facts: allFacts }).status, "incompatible-design");
const early = bindHierarchyPhysicsProtocolToExecution(launch,
  { scenarioId: "iqc", pipelineStage: 0 });
assert.equal(buildHierarchyPhysicsProtocolConformance(early,
  { facts: allFacts }).status, "design-stage-pending");
const absent = bindHierarchyPhysicsProtocolToExecution({ schema: "launch", status: "absent",
  digestVerified: false, capturedBeforeAppInitialization: true },
{ scenarioId: "iqc", pipelineStage: 4 });
assert.equal(buildHierarchyPhysicsProtocolConformance(absent, { facts: {} }).status,
  "no-verified-design");

assert.deepEqual(hierarchyPhysicsProtocolConformanceChannels(), [
  "colored-geometry", "proper-pose", "connection-topology", "steric-exclusion",
  "composition", "residuals", "local-response", "interface", "kinetics", "nonlocal",
]);
for (const channel of hierarchyPhysicsProtocolConformanceChannels()) {
  for (const stage of ["atomic", "cluster", "macro", "stationary"]) {
    assert.ok(hierarchyPhysicsProtocolConformanceRequirements(channel, stage).length >= 3);
  }
}

console.log("hierarchy physics protocol conformance passed");
