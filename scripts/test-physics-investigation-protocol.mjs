import assert from "node:assert/strict";
import { buildPhysicsInvestigationProtocol } from "../apps/iqc-growth-live/physics-compression-map.js";

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
assert.equal(planned.completeManifestRecordCount, 5);
assert.equal(planned.selectionMadeBeforeCandidateEnumeration, true);

const evidenceOnly = buildPhysicsInvestigationProtocol(records, ["local-symmetry"],
  { intent: "evidence-audit" });
assert.equal(evidenceOnly.state, "evidence-only");
assert.equal(evidenceOnly.readyToExecute, false);

assert.throws(() => buildPhysicsInvestigationProtocol(records, ["steric", "steric"]), /duplicate/);
assert.throws(() => buildPhysicsInvestigationProtocol(records, ["unknown"]), /unknown IDs/);
assert.throws(() => buildPhysicsInvestigationProtocol(records, [], { intent: "physical-time" }), /unsupported/);

console.log("physics investigation protocol regression passed", {
  ready: ready.selectedRecordCount,
  planned: planned.readinessCounts,
  effects: planned.executionObjectsCovered,
});
