import assert from "node:assert/strict";
import { buildHierarchyPhysicsProtocolPacket, hierarchyPhysicsProtocolShareUrl }
  from "../apps/iqc-growth-live/hierarchy-physics-protocol-packet.mjs";
import { captureHierarchyPhysicsProtocolLaunch, bindHierarchyPhysicsProtocolToExecution,
  hierarchyPhysicsProtocolLaunchAuditFromPacket }
  from "../apps/iqc-growth-live/hierarchy-physics-execution-binding.mjs";

const packet = await buildHierarchyPhysicsProtocolPacket("iqc-reencoding", "kinetics", "stationary");
const link = hierarchyPhysicsProtocolShareUrl("https://example.test/lab?material=iqc&stage=4", packet);
const verified = await captureHierarchyPhysicsProtocolLaunch(new URL(link).search);
assert.equal(verified.status, "verified");
assert.equal(verified.actualSha256,
  "313cbd1d7eff7c5e10b7b6f3436ecaf15297138531cc3d399fb811c4c8143a74");
assert.equal(verified.capturedBeforeAppInitialization, true);
assert.equal(verified.targetUsed, false);
assert.equal(verified.coordinatesEmbedded, false);
assert.deepEqual(hierarchyPhysicsProtocolLaunchAuditFromPacket({ ...verified.selection,
  expectedSha256: verified.expectedSha256 }, packet), verified);
assert.throws(() => hierarchyPhysicsProtocolLaunchAuditFromPacket({ ...verified.selection,
  expectedSha256: verified.expectedSha256 }, { ...packet,
  selection: { ...packet.selection, stageId: "macro" } }), /does not match/);

const awaiting = bindHierarchyPhysicsProtocolToExecution(verified,
  { scenarioId: "iqc", pipelineStage: 0, receiptBuildId: "20260901-411" });
assert.equal(awaiting.status, "verified-design-awaiting-stage");
assert.equal(awaiting.designReferenceBoundToReceipt, true);
assert.equal(awaiting.currentRunCompatible, true);
assert.equal(awaiting.plannedStageReached, false);
assert.equal(awaiting.executionAuthorizedByPacket, false);
assert.equal(awaiting.executionConformanceClaimed, false);
assert.equal(awaiting.greenGateEvaluated, false);
assert.equal(awaiting.greenGateSatisfied, null);
assert.equal(awaiting.outcomeClaimUpgraded, false);

const reached = bindHierarchyPhysicsProtocolToExecution(verified,
  { scenarioId: "iqc", pipelineStage: 4, receiptBuildId: "20260901-411" });
assert.equal(reached.status, "verified-design-stage-reached");
assert.equal(reached.plannedStageReached, true);
assert.equal(reached.greenGateEvaluated, false);

const mismatch = bindHierarchyPhysicsProtocolToExecution(verified,
  { scenarioId: "competition", pipelineStage: 4, receiptBuildId: "20260901-411" });
assert.equal(mismatch.status, "material-mismatch");
assert.equal(mismatch.currentRunCompatible, false);

const badSearch = new URL(link);
badSearch.searchParams.set("bridgeSha256", "0".repeat(64));
const badDigest = await captureHierarchyPhysicsProtocolLaunch(badSearch.search);
assert.equal(badDigest.status, "mismatch");
assert.equal(bindHierarchyPhysicsProtocolToExecution(badDigest,
  { scenarioId: "iqc", pipelineStage: 4 }).status, "design-packet-rejected");

const incomplete = await captureHierarchyPhysicsProtocolLaunch(
  "?bridgeReceipt=iqc-reencoding&bridgeChannel=kinetics");
assert.equal(incomplete.status, "invalid");
const absent = await captureHierarchyPhysicsProtocolLaunch("?material=iqc");
assert.equal(absent.status, "absent");
assert.equal(bindHierarchyPhysicsProtocolToExecution(absent,
  { scenarioId: "iqc", pipelineStage: 4 }).status, "no-design-packet");

assert.throws(() => bindHierarchyPhysicsProtocolToExecution(null,
  { scenarioId: "iqc", pipelineStage: 4 }), /launch audit/);
assert.throws(() => bindHierarchyPhysicsProtocolToExecution(verified,
  { scenarioId: "", pipelineStage: 4 }), /scenario ID/);
assert.throws(() => bindHierarchyPhysicsProtocolToExecution(verified,
  { scenarioId: "iqc", pipelineStage: 8 }), /pipeline stage/);

console.log("hierarchy physics execution binding passed");
