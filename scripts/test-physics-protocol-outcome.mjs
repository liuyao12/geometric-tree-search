import assert from "node:assert/strict";
import { comparePhysicsProtocolOutcomes }
  from "../apps/iqc-growth-live/physics-protocol-outcome.js";

const plan = {
  schema: 2,
  state: "ready-to-configure",
  executableLayer: true,
  comparisonMode: "matched-candidate-ranking",
  ablatedRecordId: "surface",
  ablatedProcess: "surface completion",
  changedExecutionObjects: ["ranking"],
  baselineSelectedRecordIds: ["steric", "surface"],
  ablationSelectedRecordIds: ["steric"],
  candidateSetMustRemainIdentical: true,
  candidateSetMayChange: false,
  initialStateMayChange: false,
  candidateIdentityGate: "first-frontier candidate digest must match",
  controlBinding: {
    schema: 1,
    state: "ready-to-configure",
    readyToConfigure: true,
    recordId: "surface",
    controlId: "surfacePreferenceSelect",
    interventionKind: "explicit-neutral-control-value",
    baselineValue: "soft",
    ablationValue: "none",
    affectedRecordIds: ["surface"],
    selectedAffectedRecordIds: ["surface"],
    exactlyOneControlChanges: true,
    changedControlIds: ["surfacePreferenceSelect"],
  },
};

function entry(id, arm, overrides = {}) {
  const baseline = arm === "baseline";
  const point = (atoms, clusters, accepted, rejected, prominence, q6) => ({
    atoms, clusters, frontier: 12, depth: 1, cumulativeAccepted: accepted,
    cumulativeRejected: rejected,
    scattering: { summary: { peakProminence: prominence } },
    orientationalOrder: { harmonics: [{ order: 6, mean: q6 }] },
  });
  return {
    id,
    inputIdentity: "sample:sha256",
    interventionFactors: { boundary: { value: "same-public-boundary" } },
    executionEvidence: {
      executed: true, structuralLeapEvents: 2,
      seedProtocolMode: "observed-window",
      seedConfigurationDigest: "seed-digest",
      seedTargetUsed: false,
      firstFrontierCandidateSetDigest: "candidate-digest",
      firstFrontierTargetUsed: false, targetUsed: false,
    },
    trajectory: {
      historyTruncated: false, targetUsed: false,
      points: baseline
        ? [point(100, 4, 0, 0, 1.1, .31), point(112, 6, 4, 2, 1.3, .35), point(126, 8, 8, 4, 1.6, .39)]
        : [point(100, 4, 0, 0, 1.1, .31), point(109, 5, 3, 3, 1.2, .33), point(118, 7, 6, 7, 1.35, .34)],
    },
    physicsProtocolExperiment: {
      schema: 1,
      preflightManifestSchema: 4,
      preflightManifestSha256: `${arm}-manifest`,
      interventionPlan: structuredClone(plan),
      armRegistration: {
        schema: 1,
        ablatedRecordId: "surface",
        activeArm: arm,
        baselineSelectedRecordIds: ["steric", "surface"],
        activeSelectedRecordIds: baseline ? ["steric", "surface"] : ["steric"],
        controlId: "surfacePreferenceSelect",
        baselineValue: "soft",
        ablationValue: "none",
        appliedControlValue: baseline ? "soft" : "none",
        controlValueMatchesActiveArm: true,
        exactlyOneControlChanges: true,
        changedControlIds: ["surfacePreferenceSelect"],
        configuredBeforeCandidateEnumeration: true,
        candidateSetInspected: false,
        targetUsed: false,
      },
      controlVector: {
        schema: 1,
        values: { surfacePreferenceSelect: baseline ? "soft" : "none", thermalFieldSelect: "none" },
        controlCount: 2,
        capturedBeforeCandidateEnumeration: true,
        candidateSetInspected: false,
        targetUsed: false,
      },
      frozenBeforeFirstStructuralAction: true,
      targetUsed: false,
    },
    ...overrides,
  };
}

const baseline = entry("baseline", "baseline");
const ablation = entry("ablation", "ablation");
const matched = comparePhysicsProtocolOutcomes([ablation, baseline]);
assert.equal(matched.comparable, true);
assert.equal(matched.status, "matched");
assert.equal(matched.baselineEntryId, "baseline");
assert.equal(matched.ablationEntryId, "ablation");
assert.equal(matched.commonUpdates, 2);
assert.deepEqual(matched.changedControlIds, ["surfacePreferenceSelect"]);
assert.equal(matched.candidateIdentity.passed, true);
assert.equal(matched.candidateIdentity.gate, "identical");
assert.equal(matched.seedIdentity.passed, true);
assert.equal(matched.metrics.find((metric) => metric.label === "explicit structural sites").delta, -8);
assert.equal(matched.metrics.find((metric) => metric.label === "rejected actions").delta, 3);
assert.equal(matched.targetUsed, false);
assert.equal(matched.searchReplayed, false);
assert.equal(matched.physicalTimeInferred, false);

const drift = structuredClone(ablation);
drift.physicsProtocolExperiment.controlVector.values.thermalFieldSelect = "gradient";
assert.equal(comparePhysicsProtocolOutcomes([baseline, drift]).reason, "controls-mismatch");

const candidateMismatch = structuredClone(ablation);
candidateMismatch.executionEvidence.firstFrontierCandidateSetDigest = "different";
assert.equal(comparePhysicsProtocolOutcomes([baseline, candidateMismatch]).reason,
  "candidate-identity-mismatch");

const seedMismatch = structuredClone(ablation);
seedMismatch.executionEvidence.seedConfigurationDigest = "different-seed";
assert.equal(comparePhysicsProtocolOutcomes([baseline, seedMismatch]).reason, "seed-mismatch");

const targetFrontier = structuredClone(ablation);
targetFrontier.executionEvidence.firstFrontierTargetUsed = true;
assert.equal(comparePhysicsProtocolOutcomes([baseline, targetFrontier]).reason,
  "candidate-frontier-target-tainted");

const targetTainted = structuredClone(ablation);
targetTainted.trajectory.targetUsed = true;
assert.equal(comparePhysicsProtocolOutcomes([baseline, targetTainted]).reason, "target-tainted");

const unfrozen = structuredClone(ablation);
unfrozen.physicsProtocolExperiment.frozenBeforeFirstStructuralAction = false;
assert.equal(comparePhysicsProtocolOutcomes([baseline, unfrozen]).reason, "preflight-not-frozen");

const truncated = structuredClone(ablation);
truncated.trajectory.historyTruncated = true;
assert.equal(comparePhysicsProtocolOutcomes([baseline, truncated]).reason, "history-truncated");

const initialState = structuredClone(ablation);
initialState.physicsProtocolExperiment.interventionPlan.changedExecutionObjects = ["initialState"];
initialState.physicsProtocolExperiment.interventionPlan.comparisonMode = "matched-input-structural-response";
initialState.physicsProtocolExperiment.interventionPlan.candidateSetMustRemainIdentical = false;
initialState.physicsProtocolExperiment.interventionPlan.initialStateMayChange = true;
const baselineInitial = structuredClone(baseline);
baselineInitial.physicsProtocolExperiment.interventionPlan = structuredClone(
  initialState.physicsProtocolExperiment.interventionPlan);
assert.equal(comparePhysicsProtocolOutcomes([baselineInitial, initialState]).reason,
  "seed-identity-unavailable");

assert.equal(comparePhysicsProtocolOutcomes([baseline]).reason, "select-two");
console.log("physics protocol matched-outcome regression passed", {
  comparison: matched.comparisonDigest,
  controls: matched.changedControlIds,
  horizon: matched.commonUpdates,
});
