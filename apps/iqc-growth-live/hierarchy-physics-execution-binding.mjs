import { buildHierarchyPhysicsProtocolPacket, hierarchyPhysicsProtocolSelectionFromSearch }
  from "./hierarchy-physics-protocol-packet.mjs?v=20260831-408";

export async function captureHierarchyPhysicsProtocolLaunch(search) {
  let selection;
  try { selection = hierarchyPhysicsProtocolSelectionFromSearch(search); }
  catch (error) {
    return Object.freeze({ schema: "gcts-hierarchy-physics-protocol-launch-v1",
      status: "invalid", reason: error.message, selection: null, expectedSha256: null,
      actualSha256: null, digestVerified: false, capturedBeforeAppInitialization: true,
      targetUsed: false, coordinatesEmbedded: false, candidateActionsEmbedded: false });
  }
  if (!selection) return Object.freeze({
    schema: "gcts-hierarchy-physics-protocol-launch-v1", status: "absent",
    reason: "No scale-bridge protocol parameters were present at launch.", selection: null,
    expectedSha256: null, actualSha256: null, digestVerified: false,
    capturedBeforeAppInitialization: true, targetUsed: false,
    coordinatesEmbedded: false, candidateActionsEmbedded: false });
  const packet = await buildHierarchyPhysicsProtocolPacket(
    selection.receiptId, selection.channelId, selection.stageId);
  return hierarchyPhysicsProtocolLaunchAuditFromPacket(selection, packet);
}

export function hierarchyPhysicsProtocolLaunchAuditFromPacket(selection, packet) {
  if (!selection || !/^[0-9a-f]{64}$/.test(selection.expectedSha256 || "")) {
    throw new TypeError("A parsed protocol selection with expected SHA-256 is required.");
  }
  if (!packet?.selection || !/^[0-9a-f]{64}$/.test(packet.sha256 || "")) {
    throw new TypeError("A canonical hashed protocol packet is required.");
  }
  if (packet.selection.receiptId !== selection.receiptId
    || packet.selection.channelId !== selection.channelId
    || packet.selection.stageId !== selection.stageId) {
    throw new Error("Protocol packet selection does not match the captured launch selection.");
  }
  const digestVerified = packet.sha256 === selection.expectedSha256;
  return Object.freeze({
    schema: "gcts-hierarchy-physics-protocol-launch-v1",
    status: digestVerified ? "verified" : "mismatch",
    reason: digestVerified ? "Canonical design packet matches the launch SHA-256."
      : "Canonical design packet does not match the launch SHA-256.",
    selection: Object.freeze({ receiptId: selection.receiptId,
      channelId: selection.channelId, stageId: selection.stageId }),
    expectedSha256: selection.expectedSha256, actualSha256: packet.sha256,
    digestVerified, packetBuild: packet.build, transportStatus: packet.source.transportStatus,
    route: packet.investigation.route, currentClaimAllowed: packet.claim.currentlyAllowed,
    claimBoundary: packet.claim.boundary, capturedBeforeAppInitialization: true,
    packetCanonicalJsonEmbedded: false, targetUsed: false,
    coordinatesEmbedded: false, candidateActionsEmbedded: false,
  });
}

export function bindHierarchyPhysicsProtocolToExecution(launchAudit,
  { scenarioId, pipelineStage, receiptBuildId } = {}) {
  if (!launchAudit?.schema) throw new TypeError("A launch audit is required.");
  if (typeof scenarioId !== "string" || !scenarioId) throw new TypeError("A current scenario ID is required.");
  if (!Number.isInteger(pipelineStage) || pipelineStage < 0 || pipelineStage > 4) {
    throw new TypeError("A valid pipeline stage is required.");
  }
  const verified = launchAudit.status === "verified" && launchAudit.digestVerified;
  const scenarioMatches = verified ? launchAudit.route.scenario === scenarioId : null;
  const plannedStageReached = verified ? pipelineStage >= launchAudit.route.stage : null;
  const currentRunCompatible = verified && scenarioMatches;
  const status = launchAudit.status === "absent" ? "no-design-packet"
    : !verified ? "design-packet-rejected"
      : !scenarioMatches ? "material-mismatch"
        : !plannedStageReached ? "verified-design-awaiting-stage" : "verified-design-stage-reached";
  return Object.freeze({
    schema: "gcts-hierarchy-physics-execution-binding-v1", status,
    launchStatus: launchAudit.status, selection: launchAudit.selection,
    expectedPacketSha256: launchAudit.expectedSha256,
    verifiedPacketSha256: verified ? launchAudit.actualSha256 : null,
    digestVerified: verified, capturedBeforeAppInitialization: launchAudit.capturedBeforeAppInitialization,
    currentScenarioId: scenarioId, plannedScenarioId: verified ? launchAudit.route.scenario : null,
    scenarioMatches, currentPipelineStage: pipelineStage,
    plannedRouteStage: verified ? launchAudit.route.stage : null, plannedStageReached,
    designReferenceBoundToReceipt: verified, currentRunCompatible,
    executionReceiptBuildId: receiptBuildId || null,
    packetCanonicalJsonEmbedded: false, coordinatesEmbedded: false,
    candidateActionsEmbedded: false, targetUsedForBinding: false,
    executionAuthorizedByPacket: false, executionConformanceClaimed: false,
    greenGateEvaluated: false, greenGateSatisfied: null,
    outcomeClaimUpgraded: false, physicalTimeClaimed: false,
    claimBoundary: verified ? `${launchAudit.claimBoundary} This run receipt cites the design packet, but does not establish protocol conformance or satisfy its green gate.`
      : "No verified scale-bridge design is bound to this run. The ordinary stage-aware receipt remains valid on its own.",
  });
}
