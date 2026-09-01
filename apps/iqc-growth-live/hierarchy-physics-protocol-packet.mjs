import { buildHierarchyPhysicsInvestigation, hierarchyPhysicsInvestigationPrograms }
  from "./hierarchy-physics-investigation.mjs?v=20260901-444";

const RECEIPTS = Object.freeze(["iqc-reencoding", "iqc-compression", "cdyb-transfer", "nacl-stationary"]);
const STAGES = Object.freeze(["atomic", "cluster", "macro", "stationary"]);

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonicalValue(value[key])]));
  if (typeof value === "number" && !Number.isFinite(value)) throw new TypeError("Protocol packet numbers must be finite.");
  if (["string", "number", "boolean"].includes(typeof value) || value === null) return value;
  throw new TypeError("Protocol packet values must be JSON serializable.");
}

export function canonicalHierarchyPhysicsProtocolJson(value) {
  return JSON.stringify(canonicalValue(value));
}

async function sha256Hex(text) {
  if (!globalThis.crypto?.subtle) throw new Error("Web Crypto SHA-256 is unavailable.");
  const bytes = new TextEncoder().encode(text);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function validateSelection(receiptId, channelId, stageId) {
  if (!RECEIPTS.includes(receiptId)) throw new TypeError(`Unknown protocol receipt: ${receiptId}`);
  if (!hierarchyPhysicsInvestigationPrograms().includes(channelId)) {
    throw new TypeError(`Unknown protocol channel: ${channelId}`);
  }
  if (!STAGES.includes(stageId)) throw new TypeError(`Unknown protocol stage: ${stageId}`);
}

export async function buildHierarchyPhysicsProtocolPacket(receiptId = "iqc-reencoding",
  channelId = "colored-geometry", stageId = "macro") {
  validateSelection(receiptId, channelId, stageId);
  const plan = buildHierarchyPhysicsInvestigation(receiptId, channelId, stageId);
  if (!plan.candidateGeometryFrozenDuringAblation || plan.targetUsedForFitOrSelection) {
    throw new Error("Only leakage-safe frozen-candidate plans can become protocol packets.");
  }
  const unsigned = Object.freeze({
    schema: "gcts-hierarchy-physics-protocol-packet-v1",
    build: "20260831-391",
    selection: Object.freeze({ receiptId, channelId, stageId }),
    source: Object.freeze({ receiptTitle: plan.title, physicalChannel: plan.physical,
      scale: plan.stageLabel, transportStatus: plan.status, transportStatusLabel: plan.statusLabel }),
    investigation: Object.freeze({ question: plan.question, requiredEvidence: plan.evidence,
      geometricEncoding: plan.encoding, sealedValidation: plan.validation,
      executionHook: plan.execution, greenGate: plan.greenGate, operator: plan.operator,
      externalEvidenceRequired: plan.externalEvidenceRequired, nextAction: plan.nextAction,
      route: Object.freeze({ scenario: plan.route.scenario, stage: plan.route.stage,
        focusId: plan.route.focusId, label: plan.route.label }) }),
    invariants: Object.freeze({ candidateGeometryFrozenDuringAblation: true,
      targetUsedForFitOrSelection: false, hierarchyDepthUpgradesClaim: false,
      planOnly: true, executionAuthorized: false, executionReceiptRequired: true,
      physicalTimeClaimed: false }),
    claim: Object.freeze({ currentlyAllowed: plan.claimAllowed,
      boundary: plan.claimBoundary }),
  });
  const canonicalUnsignedJson = canonicalHierarchyPhysicsProtocolJson(unsigned);
  const sha256 = await sha256Hex(canonicalUnsignedJson);
  return Object.freeze({ ...unsigned, sha256, canonicalUnsignedJson,
    canonicalPacketJson: canonicalHierarchyPhysicsProtocolJson({ ...unsigned, sha256 }) });
}

export function hierarchyPhysicsProtocolShareUrl(baseUrl, packet) {
  if (!packet || !/^[0-9a-f]{64}$/.test(packet.sha256 || "")) throw new TypeError("A hashed protocol packet is required.");
  const url = new URL(baseUrl);
  url.searchParams.set("bridgeReceipt", packet.selection.receiptId);
  url.searchParams.set("bridgeChannel", packet.selection.channelId);
  url.searchParams.set("bridgeScale", packet.selection.stageId);
  url.searchParams.set("bridgeSha256", packet.sha256);
  return url.href;
}

export function hierarchyPhysicsProtocolSelectionFromSearch(search) {
  const parameters = new URLSearchParams(search);
  const keys = ["bridgeReceipt", "bridgeChannel", "bridgeScale", "bridgeSha256"];
  if (!keys.some((key) => parameters.has(key))) return null;
  if (!keys.every((key) => parameters.has(key))) throw new TypeError("Shared scale-bridge protocol parameters are incomplete.");
  const selection = { receiptId: parameters.get("bridgeReceipt"),
    channelId: parameters.get("bridgeChannel"), stageId: parameters.get("bridgeScale"),
    expectedSha256: parameters.get("bridgeSha256") };
  validateSelection(selection.receiptId, selection.channelId, selection.stageId);
  if (!/^[0-9a-f]{64}$/.test(selection.expectedSha256)) throw new TypeError("Shared scale-bridge SHA-256 is invalid.");
  return Object.freeze(selection);
}

export function hierarchyPhysicsProtocolPacketFilename(packet) {
  if (!packet?.selection) throw new TypeError("A protocol packet is required.");
  return `gcts-scale-bridge-${packet.selection.receiptId}-${packet.selection.channelId}-${packet.selection.stageId}-${packet.sha256.slice(0, 12)}.json`;
}
