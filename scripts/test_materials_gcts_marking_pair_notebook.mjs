import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const source = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const start = source.indexOf("function notebookRegisteredMarkingPairAudit");
const end = source.indexOf("function notebookRegisteredPairAudit", start);
assert.ok(start >= 0 && end > start, "registered marking-pair audit must be extractable");
const context = {};
vm.runInNewContext(source.slice(start, end), context);

const artifactPair = {
  baseline: { id: "marking-1", name: "scalar", artifactDigest: "artifact-a" },
  alternative: { id: "marking-2", name: "oriented", artifactDigest: "artifact-b" },
};
const registration = (arm) => ({
  schema: 1,
  experimentKind: "saved-marking intervention",
  ...artifactPair,
  arm,
  registrationDigest: "registered-pair",
  sourceCandidateSetDigest: "source-candidates",
  sourceHardAdmittedSetDigest: "source-hard",
  growthSettingsJson: "frozen-controls",
  scenarioId: "nacl",
  materialKey: "material",
  vocabularyKey: "vocabulary",
  settingsStillMatch: true,
  activeMarkingStillMatchesArm: true,
  candidateGeometryChanged: false,
  hardAdmissionChanged: false,
  targetUsed: false,
  targetUsedToRegister: false,
  autoExecuted: false,
});
const execution = (candidate = "first-candidates", hard = "first-hard") => ({
  executed: true,
  structuralLeapEvents: 2,
  firstFrontierCandidateSetDigest: candidate,
  firstFrontierHardAdmittedSetDigest: hard,
  firstFrontierTargetUsed: false,
});
const entry = (arm, executionEvidence = execution()) => ({
  markingComparisonExperiment: registration(arm),
  executionEvidence,
});
const intervention = {
  sameInput: true,
  changedFactors: [{ key: "marking", label: "GCTS marking", role: "learned representation" }],
};

const pass = context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), entry("alternative"), intervention,
);
assert.equal(pass.valid, true);
assert.equal(pass.responseComparable, true);
assert.equal(pass.firstFrontierComparable, true);
assert.equal(pass.status, "registered");

const frontierMismatch = context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), entry("alternative", execution("different", "first-hard")), intervention,
);
assert.equal(frontierMismatch.valid, true, "registration remains valid before response evidence");
assert.equal(frontierMismatch.responseComparable, false, "different executed frontiers fail closed");

const unexecuted = context.notebookRegisteredMarkingPairAudit(
  entry("baseline", { ...execution(), executed: false }), entry("alternative"), intervention,
);
assert.equal(unexecuted.valid, true);
assert.equal(unexecuted.responseComparable, false);

const mutatedArtifact = entry("alternative");
mutatedArtifact.markingComparisonExperiment.alternative = {
  ...mutatedArtifact.markingComparisonExperiment.alternative,
  artifactDigest: "mutated",
};
assert.equal(context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), mutatedArtifact, intervention,
).valid, false);

const targetTainted = entry("alternative");
targetTainted.markingComparisonExperiment.targetUsed = true;
assert.equal(context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), targetTainted, intervention,
).valid, false);

assert.equal(context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), entry("alternative"),
  { sameInput: true, changedFactors: [{ key: "ranking" }] },
).valid, false);

console.log("marking pair notebook executable audit passed");
