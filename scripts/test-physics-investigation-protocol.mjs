import assert from "node:assert/strict";
import { buildPhysicsInvestigationProtocol, buildPhysicsProtocolIntervention }
  from "../apps/iqc-growth-live/physics-compression-map.js";

const records = [
  { id: "steric", process: "excluded volume", status: "hard", role: "active",
    encoding: "minimum separation", evidence: "exact", boundary: "not energy" },
  { id: "capillary-geometry", process: "capillary hypothesis", status: "soft", role: "disabled",
    encoding: "curvature rank", evidence: "declared", boundary: "not surface energy",
    controlRouteAvailable: true, controlRouteLabel: "Configure capillary hypothesis" },
  { id: "calculation-forces", process: "archived forces", status: "unavailable", role: "awaiting input",
    encoding: "displacement seed", evidence: "missing", boundary: "not force integration",
    controlRouteAvailable: true, controlRouteLabel: "Load force evidence" },
  { id: "local-symmetry", process: "local symmetry", status: "observed", role: "diagnostic evidence",
    encoding: "symmetry score", evidence: "observed", boundary: "no execution hook" },
  { id: "long-range", process: "long-range response", status: "open", role: "unresolved",
    encoding: "not encoded", evidence: "none", boundary: "external solver" },
  { id: "surface", process: "surface completion", status: "learned", role: "active",
    encoding: "undercoordination rank", evidence: "learned", boundary: "not surface energy",
    controlRouteAvailable: true, controlRouteLabel: "Configure surface completion" },
  { id: "path-ensemble", process: "path ensemble", status: "sampled", role: "active",
    encoding: "branch order", evidence: "declared", boundary: "not stochastic dynamics",
    controlRouteAvailable: true, controlRouteLabel: "Configure path ensemble" },
];

const ready = buildPhysicsInvestigationProtocol(records, ["steric"]);
assert.equal(ready.readyToExecute, true);
assert.equal(ready.state, "ready");
assert.deepEqual(ready.executionObjectsCovered, ["hardAdmission"]);
assert.deepEqual(ready.executableRecordIds, ["steric"]);
assert.equal(ready.targetUsed, false);
assert.equal(ready.candidateSetInspected, false);

const planned = buildPhysicsInvestigationProtocol(records,
  ["steric", "capillary-geometry", "calculation-forces", "local-symmetry", "long-range"],
  { intent: "hypothesis-comparison" });
assert.equal(planned.readyToExecute, false);
assert.equal(planned.state, "external-physics-required");
assert.deepEqual(planned.readinessCounts, {
  executing: 1, configurable: 1, missingEvidence: 1, evidenceOnly: 1, external: 1,
});
assert.deepEqual(planned.blockingRecordIds,
  ["capillary-geometry", "calculation-forces", "long-range"]);
assert.deepEqual(planned.evidenceOnlyRecordIds, ["local-symmetry"]);
assert.equal(planned.effectCoverage.diagnostic.count, 4);
assert.equal(planned.completeManifestRecordCount, 7);
assert.equal(planned.selectionMadeBeforeCandidateEnumeration, true);

const evidenceOnly = buildPhysicsInvestigationProtocol(records, ["local-symmetry"],
  { intent: "evidence-audit" });
assert.equal(evidenceOnly.state, "evidence-only");
assert.equal(evidenceOnly.readyToExecute, false);

assert.throws(() => buildPhysicsInvestigationProtocol(records, ["steric", "steric"]), /duplicate/);
assert.throws(() => buildPhysicsInvestigationProtocol(records, ["unknown"]), /unknown IDs/);
assert.throws(() => buildPhysicsInvestigationProtocol(records, [], { intent: "physical-time" }), /unsupported/);

const paired = buildPhysicsInvestigationProtocol(records, ["steric", "surface", "path-ensemble"]);
const rankingIntervention = buildPhysicsProtocolIntervention(paired, "surface");
assert.equal(rankingIntervention.state, "ready-to-configure");
assert.equal(rankingIntervention.comparisonMode, "matched-candidate-ranking");
assert.equal(rankingIntervention.candidateSetMustRemainIdentical, true);
assert.equal(rankingIntervention.candidateSetMayChange, false);
assert.deepEqual(rankingIntervention.changedExecutionObjects, ["ranking"]);
assert.deepEqual(rankingIntervention.ablationSelectedRecordIds, ["steric", "path-ensemble"]);

const hardIntervention = buildPhysicsProtocolIntervention(paired, "steric");
assert.equal(hardIntervention.state, "design-only-no-control");
assert.equal(hardIntervention.comparisonMode, "matched-input-structural-response");
assert.equal(hardIntervention.candidateSetMustRemainIdentical, false);
assert.equal(hardIntervention.candidateSetMayChange, true);
assert.match(hardIntervention.candidateIdentityGate, /outcome/);

const orderIntervention = buildPhysicsProtocolIntervention(paired, "path-ensemble");
assert.equal(orderIntervention.candidateSetMustRemainIdentical, true);
assert.deepEqual(orderIntervention.changedExecutionObjects, ["searchOrder"]);
assert.throws(() => buildPhysicsProtocolIntervention(paired, "long-range"), /not selected/);

console.log("physics investigation protocol regression passed", {
  ready: ready.selectedRecordCount,
  planned: planned.readinessCounts,
  effects: planned.executionObjectsCovered, rankingMode: rankingIntervention.comparisonMode,
});
