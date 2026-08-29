import assert from "node:assert/strict";
import { auditCoverConnectionEvidence, connectionEvidenceNarrative }
  from "../apps/iqc-growth-live/connection-evidence.mjs";

const direct = auditCoverConnectionEvidence({
  placements: [{ type: 0 }, { type: 1 }, { type: 0 }],
  edges: [{ first: 0, second: 1 }, { first: 1, second: 2 }],
  rules: [{ from: 0, to: 1, count: 3 }, { from: 1, to: 0, count: 1 }],
});
assert.equal(direct.verdict, "direct-recurrent");
assert.equal(direct.directSupportEdges, 2);
assert.equal(direct.recurringDirectRules, 1);
assert.match(connectionEvidenceNarrative(direct).label, /compressed/);

const bridged = auditCoverConnectionEvidence({
  placements: [{ type: 0 }, { type: 8, residual: true }, { type: 1 }, { type: 8, residual: true }, { type: 0 }],
  edges: [
    { first: 0, second: 1 }, { first: 1, second: 2 },
    { first: 2, second: 3 }, { first: 3, second: 4 },
  ],
});
assert.equal(bridged.verdict, "terminal-mediated");
assert.equal(bridged.supportTerminalEdges, 4);
assert.equal(bridged.terminalBridgeOccurrencePairs, 2);
assert.equal(bridged.terminalBridgeTypePairs, 1);
assert.equal(bridged.recurringBridgeTopologies, 1);
assert.match(connectionEvidenceNarrative(bridged).implication, /representation frontier/);

const isolated = auditCoverConnectionEvidence({ placements: [{ type: 0 }, { type: 1 }], edges: [] });
assert.equal(isolated.verdict, "no-shared-interface");
assert.equal(isolated.isolatedPromotableOccurrences, 2);

assert.throws(() => auditCoverConnectionEvidence({
  placements: [{ type: 0 }], edges: [{ first: 0, second: 1 }],
}), /invalid occurrence/);

console.log("connection evidence audit contract: pass");
