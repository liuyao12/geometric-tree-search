import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const source = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const start = source.indexOf("function notebookRegisteredMarkingPairAudit");
const end = source.indexOf("function notebookRegisteredPairAudit", start);
assert.ok(start >= 0 && end > start, "registered marking-pair audit must be extractable");
const context = {};
vm.runInNewContext(source.slice(start, end), context);

const validationStart = source.indexOf("function validateMarkingComparisonExperiment");
const validationEnd = source.indexOf("function markingComparisonSettingsStillMatch", validationStart);
const horizonStart = source.indexOf("function enforceMarkingComparisonHorizon");
const horizonEnd = source.indexOf("function configureMarkingComparisonArm", horizonStart);
assert.ok(validationStart >= 0 && validationEnd > validationStart && horizonStart >= 0 && horizonEnd > horizonStart);

const artifactPair = {
  baseline: { id: "marking-1", name: "scalar", artifactDigest: "artifact-a" },
  alternative: { id: "marking-2", name: "oriented", artifactDigest: "artifact-b" },
};
const registration = (arm) => ({
  schema: 1,
  experimentKind: "saved-marking intervention",
  ...artifactPair,
  arm,
  comparisonHorizonLeaps: 4,
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
  structuralLeapEvents: 4,
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

const terminalBaseline = entry("baseline", { ...execution(), structuralLeapEvents: 2, fixedPointObserved: true });
const terminalAlternative = entry("alternative", { ...execution(), structuralLeapEvents: 3, fixedPointObserved: true });
const terminalPair = context.notebookRegisteredMarkingPairAudit(
  terminalBaseline, terminalAlternative, intervention,
);
assert.equal(terminalPair.responseComparable, true, "two earlier audited fixed points are comparable");
assert.equal(terminalPair.matchedTerminalFixedPoints, true);
const censoredAlternative = entry("alternative", { ...execution(), structuralLeapEvents: 3, fixedPointObserved: false });
assert.equal(context.notebookRegisteredMarkingPairAudit(
  terminalBaseline, censoredAlternative, intervention,
).responseComparable, false, "one fixed point versus one censored frontier fails closed");

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

const horizonSignals = { playing: true, rendered: 0, buttonsUpdated: 0 };
const horizonContext = {
  pipelineStage: 4,
  leapEventCount: 4,
  markingComparisonExperiment: registration("baseline"),
  growthStopReason: "",
  pipelineAuto: true,
  setPlaying(value) { horizonSignals.playing = value; },
  updatePipelineButtons() { horizonSignals.buttonsUpdated += 1; },
  updateUI() { horizonSignals.rendered += 1; },
};
vm.runInNewContext(source.slice(validationStart, validationEnd)
  + source.slice(horizonStart, horizonEnd), horizonContext);
assert.equal(horizonContext.enforceMarkingComparisonHorizon(), true);
assert.equal(horizonSignals.playing, false);
assert.equal(horizonContext.pipelineAuto, false);
assert.match(horizonContext.growthStopReason, /frozen 4-leap comparison horizon/);
assert.equal(horizonSignals.buttonsUpdated, 1);
assert.equal(horizonSignals.rendered, 0);
horizonContext.leapEventCount = 3;
assert.equal(horizonContext.enforceMarkingComparisonHorizon(true), false);
assert.equal(horizonSignals.rendered, 0);

const targetTainted = entry("alternative");
targetTainted.markingComparisonExperiment.targetUsed = true;
assert.equal(context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), targetTainted, intervention,
).valid, false);

const mismatchedHorizon = entry("alternative");
mismatchedHorizon.markingComparisonExperiment.comparisonHorizonLeaps = 8;
assert.equal(context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), mismatchedHorizon, intervention,
).valid, false);

assert.equal(context.notebookRegisteredMarkingPairAudit(
  entry("baseline"), entry("alternative"),
  { sameInput: true, changedFactors: [{ key: "ranking" }] },
).valid, false);

console.log("marking pair notebook executable audit passed");
