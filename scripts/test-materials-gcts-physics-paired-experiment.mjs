import assert from "node:assert/strict";
import { buildPhysicsProtocolPairProgress, buildPhysicsProtocolResponseFingerprint,
  comparePhysicsProtocolOutcomes }
  from "../apps/iqc-growth-live/physics-protocol-outcome.js";

const selected = ["constraint-projection", "connection", "steric"];
const ablationSelected = ["connection", "steric"];
const plan = {
  schema: 1,
  state: "ready-to-configure",
  armConfigurationReady: true,
  executableLayer: true,
  comparisonMode: "matched-input-structural-response",
  ablatedRecordId: "constraint-projection",
  ablatedProcess: "post-attachment local structural accommodation",
  changedExecutionObjects: ["bounded candidate site coordinates"],
  baselineSelectedRecordIds: selected,
  ablationSelectedRecordIds: ablationSelected,
  candidateSetMustRemainIdentical: false,
  candidateSetMayChange: true,
  initialStateMayChange: false,
  candidateIdentityGate: "candidate set is a measured response",
  controlBinding: {
    schema: 1,
    recordId: "constraint-projection",
    controlId: "structuralRelaxationSelect",
    interventionKind: "explicit-neutral-control-value",
    baselineValue: "balanced",
    ablationValue: "off",
    affectedRecordIds: ["constraint-projection"],
    selectedAffectedRecordIds: ["constraint-projection"],
    exactlyOneControlChanges: true,
    changedControlIds: ["structuralRelaxationSelect"],
  },
};

function registration(activeArm) {
  return {
    schema: 1,
    activeArm,
    activeSelectedRecordIds: activeArm === "baseline" ? selected : ablationSelected,
    controlId: "structuralRelaxationSelect",
    controlValueMatchesActiveArm: true,
    exactlyOneControlChanges: true,
    changedControlIds: ["structuralRelaxationSelect"],
    configuredBeforeCandidateEnumeration: true,
    candidateSetInspected: false,
    targetUsed: false,
  };
}

function entry(id, arm, value, atoms) {
  return {
    id,
    scenarioId: "competition",
    receiptSha256: `${id}-receipt`,
    inputIdentity: "same-input",
    physicsProtocolExperiment: {
      schema: 1,
      preflightManifestSchema: 5,
      frozenBeforeFirstStructuralAction: true,
      targetUsed: false,
      interventionPlan: plan,
      armRegistration: registration(arm),
      controlVector: {
        schema: 1,
        capturedBeforeCandidateEnumeration: true,
        candidateSetInspected: false,
        targetUsed: false,
        values: { structuralRelaxationSelect: value, thermalFieldSelect: "none" },
      },
    },
    executionEvidence: {
      executed: true,
      structuralLeapEvents: 1,
      seedConfigurationDigest: "same-seed",
      seedTargetUsed: false,
      firstFrontierCandidateSetDigest: `${arm}-frontier`,
      firstFrontierTargetUsed: false,
      targetUsed: false,
    },
    interventionFactors: { boundary: { value: "box-1x" } },
    trajectory: {
      targetUsed: false,
      historyTruncated: false,
      points: [
        { atoms: 100, clusters: 10, frontier: 5, depth: 0, cumulativeAccepted: 0,
          cumulativeRejected: 0, orientationalOrder: { harmonics: [{ order: 6, mean: .2 }] } },
        { atoms, clusters: 12, frontier: 4, depth: 1, cumulativeAccepted: 2,
          cumulativeRejected: 1, orientationalOrder: { harmonics: [{ order: 6, mean: .3 }] },
          scattering: { summary: { peakProminence: 2 } } },
      ],
    },
  };
}

const baseline = entry("baseline-run", "baseline", "balanced", 112);
const armB = entry("arm-b-run", "ablation", "off", 110);
const baselineProtocol = { interventionPlan: plan, armRegistration: registration("baseline") };
const ablationProtocol = { interventionPlan: plan, armRegistration: registration("ablation") };

const unregistered = buildPhysicsProtocolPairProgress({}, []);
assert.equal(unregistered.state, "registration-required");
assert.equal(unregistered.steps.length, 4);
assert.equal(unregistered.steps[0].active, true);
assert.equal(buildPhysicsProtocolPairProgress({ interventionPlan: plan }, []).state, "choose-baseline");
assert.equal(buildPhysicsProtocolPairProgress(baselineProtocol, []).state, "run-baseline");
assert.match(buildPhysicsProtocolPairProgress(baselineProtocol, [],
  { currentStructuralLeapEvents: 1 }).nextAction, /Save the executed Baseline/);
assert.equal(buildPhysicsProtocolPairProgress(baselineProtocol, [baseline]).state,
  "configure-ablation");
assert.equal(buildPhysicsProtocolPairProgress(baselineProtocol, [baseline], {
  currentScenarioId: "random", currentSeedConfigurationDigest: "other-seed",
}).state, "run-baseline");
assert.equal(buildPhysicsProtocolPairProgress(ablationProtocol, [baseline]).state,
  "run-ablation");

const matched = buildPhysicsProtocolPairProgress(ablationProtocol, [baseline, armB]);
const matchedAudit = comparePhysicsProtocolOutcomes([baseline, armB]);
assert.equal(matchedAudit.comparable, true);
assert.equal(matchedAudit.responseFingerprint.available, true);
assert.equal(matchedAudit.responseFingerprint.responseObserved, true);
assert.equal(matchedAudit.responseFingerprint.domains.length, 3);
assert.equal(matchedAudit.responseFingerprint.dominantDomainId, "extent");
assert.equal(matchedAudit.responseFingerprint.domains.find(({ id }) => id === "extent")
  .dominantMetric.label, "explicit structural sites");
assert.equal(matchedAudit.responseFingerprint.favorableDirectionAssigned, false);
assert.equal(matchedAudit.responseFingerprint.causalPhysicalMechanismInferred, false);
assert.match(matchedAudit.responseFingerprint.normalization, /Arm B − baseline/);
assert.equal(buildPhysicsProtocolResponseFingerprint({ comparable: false }).available, false);
assert.equal(matched.state, "matched");
assert.deepEqual(matched.selectedEntryIds, ["baseline-run", "arm-b-run"]);
assert.equal(matched.steps.every((step) => step.complete), true);
assert.equal(matched.targetUsed, false);
assert.equal(matched.searchExecutedByTracker, false);

const wrongSeed = structuredClone(armB);
wrongSeed.id = "arm-b-wrong-seed";
wrongSeed.executionEvidence.seedConfigurationDigest = "different-seed";
const blocked = buildPhysicsProtocolPairProgress(ablationProtocol, [baseline, wrongSeed]);
assert.equal(blocked.state, "comparison-blocked");
assert.equal(blocked.latestComparisonReason, "seed-mismatch");

console.log("physics paired experiment tests passed");
