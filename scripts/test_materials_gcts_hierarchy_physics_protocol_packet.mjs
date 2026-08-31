import assert from "node:assert/strict";
import { buildHierarchyPhysicsProtocolPacket, canonicalHierarchyPhysicsProtocolJson,
  hierarchyPhysicsProtocolShareUrl, hierarchyPhysicsProtocolSelectionFromSearch,
  hierarchyPhysicsProtocolPacketFilename }
  from "../apps/iqc-growth-live/hierarchy-physics-protocol-packet.mjs";

const packet = await buildHierarchyPhysicsProtocolPacket("iqc-reencoding", "kinetics", "stationary");
const repeated = await buildHierarchyPhysicsProtocolPacket("iqc-reencoding", "kinetics", "stationary");
assert.equal(packet.schema, "gcts-hierarchy-physics-protocol-packet-v1");
assert.equal(packet.sha256, "313cbd1d7eff7c5e10b7b6f3436ecaf15297138531cc3d399fb811c4c8143a74");
assert.equal(repeated.sha256, packet.sha256);
assert.equal(repeated.canonicalPacketJson, packet.canonicalPacketJson);
assert.deepEqual(packet.selection,
  { receiptId: "iqc-reencoding", channelId: "kinetics", stageId: "stationary" });
assert.equal(packet.source.transportStatus, "open");
assert.equal(packet.investigation.externalEvidenceRequired, true);
assert.deepEqual(packet.invariants, {
  candidateGeometryFrozenDuringAblation: true,
  targetUsedForFitOrSelection: false,
  hierarchyDepthUpgradesClaim: false,
  planOnly: true,
  executionAuthorized: false,
  executionReceiptRequired: true,
  physicalTimeClaimed: false,
});
assert.equal(packet.claim.currentlyAllowed, false);
assert.ok(!packet.canonicalPacketJson.includes("canonicalUnsignedJson"));
assert.ok(!packet.canonicalPacketJson.includes("candidateActions"));

const otherStage = await buildHierarchyPhysicsProtocolPacket("iqc-reencoding", "kinetics", "macro");
assert.notEqual(otherStage.sha256, packet.sha256);
const otherReceipt = await buildHierarchyPhysicsProtocolPacket("nacl-stationary", "colored-geometry", "stationary");
assert.equal(otherReceipt.claim.currentlyAllowed, true);
assert.notEqual(otherReceipt.sha256, packet.sha256);

const url = hierarchyPhysicsProtocolShareUrl(
  "https://example.test/lab?material=iqc&stage=4", packet);
const parsed = hierarchyPhysicsProtocolSelectionFromSearch(new URL(url).search);
assert.deepEqual(parsed, {
  receiptId: "iqc-reencoding", channelId: "kinetics", stageId: "stationary",
  expectedSha256: packet.sha256,
});
assert.equal(new URL(url).searchParams.get("material"), "iqc");
assert.equal(new URL(url).searchParams.get("stage"), "4");
assert.equal(hierarchyPhysicsProtocolSelectionFromSearch("?material=iqc"), null);
assert.match(hierarchyPhysicsProtocolPacketFilename(packet),
  /^gcts-scale-bridge-iqc-reencoding-kinetics-stationary-313cbd1d7eff\.json$/);

assert.equal(canonicalHierarchyPhysicsProtocolJson({ z: 1, a: { y: 2, b: 3 } }),
  '{"a":{"b":3,"y":2},"z":1}');
assert.throws(() => canonicalHierarchyPhysicsProtocolJson({ invalid: Infinity }), /finite/);
assert.throws(() => hierarchyPhysicsProtocolSelectionFromSearch(
  "?bridgeReceipt=iqc-reencoding&bridgeChannel=kinetics"), /incomplete/);
assert.throws(() => hierarchyPhysicsProtocolSelectionFromSearch(
  `?bridgeReceipt=iqc-reencoding&bridgeChannel=missing&bridgeScale=stationary&bridgeSha256=${packet.sha256}`),
  /Unknown protocol channel/);
assert.throws(() => hierarchyPhysicsProtocolSelectionFromSearch(
  "?bridgeReceipt=iqc-reencoding&bridgeChannel=kinetics&bridgeScale=stationary&bridgeSha256=bad"),
  /SHA-256 is invalid/);

console.log("hierarchy physics protocol packet passed");
