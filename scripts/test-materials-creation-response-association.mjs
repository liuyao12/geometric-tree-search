import assert from "node:assert/strict";
import { blockedCreationResponseValidation, buildCreationResponseAssociation,
  blockedCreationResponseSurrogate, canonicalCreationResponseDataset, creationResponseHorizonSweep,
  crossRunHorizonReadinessAtlas,
  creationResponseLeapProfile,
  LOCAL_CREATION_CONTEXT_FEATURE_IDS }
  from "../apps/iqc-growth-live/creation-response-association.js";

const records = Array.from({ length: 6 }, (_, index) => ({
  placementId: index + 1, leapIndex: Math.floor(index / 2) + 1, emittedSites: index % 2 ? 5 : 2,
  physicsTerms: [
    { id: "strain", label: "contact + angle", weight: -.2, contribution: index },
    { id: "loop", label: "loop closure", weight: .3, contribution: 5 - index },
    { id: "inactive", weight: 0, contribution: 99 },
  ],
  outcomes: { nonaffine: 2 * index, shellChange: index < 3 ? 0 : 1 },
}));
const audit = buildCreationResponseAssociation(records);
assert.equal(audit.available, true);
assert.equal(audit.placementSamples, 6);
assert.equal(audit.emittedSitePresentations, 21);
assert.equal(audit.atomLevelPseudoreplicationAvoided, true);
assert.equal(audit.independentMaterialSamples, false);
assert.equal(audit.termIds.includes("inactive"), false);
const positive = audit.associations.find((entry) => entry.termId === "strain" && entry.outcomeId === "nonaffine");
const negative = audit.associations.find((entry) => entry.termId === "loop" && entry.outcomeId === "nonaffine");
assert.equal(positive.spearmanRho, 1);
assert.equal(negative.spearmanRho, -1);
assert.equal(positive.points.length, 6);
assert.throws(() => buildCreationResponseAssociation([...records, records[0]]), /exactly once/);
assert.equal(buildCreationResponseAssociation(records.slice(0, 3), { minimumSamples: 4 }).available, false);
const canonical = canonicalCreationResponseDataset(records);
const reversedCanonical = canonicalCreationResponseDataset([...records].reverse());
assert.deepEqual(canonical, reversedCanonical);
assert.equal(canonical.records.length, 6);
assert.equal(canonical.coordinatesEmbedded, false);
assert.equal(canonical.atomIdsEmbedded, false);
assert.deepEqual(canonical.records[0].physicsTerms.map((term) => term.id), ["loop", "strain"]);
assert.equal(canonicalCreationResponseDataset(records, { maximumRecords: 3 }).truncated, true);
assert.throws(() => canonicalCreationResponseDataset([...records, records[0]]), /one record/);
const blockedRecords = Array.from({ length: 24 }, (_, index) => {
  const leapIndex = Math.floor(index / 6) + 1; const within = index % 6;
  const heldout = leapIndex >= 4;
  return { placementId: `b${index}`, leapIndex, emittedSites: 2,
    physicsTerms: [{ id: "strain", label: "strain", weight: 1, contribution: within }],
    outcomes: { shellChange: heldout ? 5 - within : within } };
});
const leapProfile = creationResponseLeapProfile(blockedRecords, "strain", "shellChange");
assert.equal(leapProfile.totalBlocks, 4);
assert.equal(leapProfile.availableBlocks, 4);
assert.deepEqual(leapProfile.blocks.map((block) => block.spearmanRho), [1, 1, 1, -1]);
assert.equal(leapProfile.signConsistentAcrossAvailableBlocks, false);
const blocked = blockedCreationResponseValidation(blockedRecords, "shellChange",
  { trainingFraction: .75, minimumSamplesPerSplit: 4 });
assert.equal(blocked.available, true);
assert.deepEqual(blocked.trainingLeaps, [1, 2, 3]);
assert.deepEqual(blocked.heldoutLeaps, [4]);
assert.equal(blocked.trainingRho, 1);
assert.equal(blocked.heldoutRho, -1);
assert.equal(blocked.signRetained, false);
assert.equal(blocked.selectionUsedHeldout, false);
assert.equal(blocked.randomSplitUsed, false);
assert.equal(blockedCreationResponseValidation(blockedRecords.slice(0, 12), "shellChange").available, false);
const surrogateRecords = Array.from({ length: 40 }, (_, index) => {
  const leapIndex = Math.floor(index / 8) + 1; const x = index % 8;
  return { placementId: `s${index}`, leapIndex, emittedSites: 2,
    physicsTerms: [{ id: "strain", label: "strain", weight: 1, contribution: x },
      { id: "nuisance", label: "nuisance", weight: 1, contribution: index % 2 },
      ...(leapIndex > 3 ? [{ id: "heldout-only", weight: 1, contribution: x }] : [])],
    outcomes: { shellChange: 1 + 2 * x } };
});
const surrogate = blockedCreationResponseSurrogate(surrogateRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01 });
assert.equal(surrogate.available, true);
assert.deepEqual(surrogate.trainingLeaps, [1, 2, 3]);
assert.deepEqual(surrogate.heldoutLeaps, [4, 5]);
assert.equal(surrogate.features.some((feature) => feature.id === "heldout-only"), false);
assert.equal(surrogate.heldoutSpearman, 1);
assert.ok(surrogate.heldoutSkillVersusTrainingMean > .99);
assert.equal(surrogate.heldoutFeatureSupportCoverage, 1);
assert.equal(surrogate.fitUsedHeldout, false);
const shiftedRecords = surrogateRecords.map((record) => record.leapIndex <= 3 ? record : ({ ...record,
  physicsTerms: record.physicsTerms.map((term) => term.id === "strain"
    ? { ...term, contribution: term.contribution + 20 } : term) }));
const shifted = blockedCreationResponseSurrogate(shiftedRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01 });
assert.equal(shifted.heldoutFeatureSupportCoverage, 0);
assert.equal(shifted.supportedHeldoutPlacements, 0);
assert.equal(shifted.unsupportedHeldoutPlacements, 16);
assert.ok(shifted.maximumStandardizedFeatureExcess > 0);
assert.equal(shifted.interpolationReadiness.state, "extrapolation-only");
assert.equal(shifted.interpolationReadiness.aggregateSkillIsInterpolationTest, false);
assert.equal(shifted.interpolationReadiness.supportedSubsetSkillAvailable, false);
const interactionRecords = Array.from({ length: 60 }, (_, index) => {
  const leapIndex = Math.floor(index / 12) + 1; const within = index % 12;
  const first = (within % 3) - 1; const second = Math.floor(within / 3) % 2 ? 1 : -1;
  return { placementId: `i${index}`, leapIndex, emittedSites: 1,
    physicsTerms: [{ id: "first", weight: 1, contribution: first },
      { id: "second", weight: 1, contribution: second }],
    outcomes: { shellChange: 3 * first * second } };
});
const interaction = blockedCreationResponseSurrogate(interactionRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01 });
assert.equal(interaction.available, true);
assert.ok(interaction.heldoutSkillVersusTrainingMean < .01);
assert.ok(interaction.quadraticControl.heldoutSkillVersusTrainingMean > .99);
assert.equal(interaction.quadraticControl.modelSelectedUsingHeldout, false);
assert.equal(interaction.quadraticControl.coefficients.some((term) => term.kind === "interaction"), true);
const contextualRecords = Array.from({ length: 60 }, (_, index) => {
  const leapIndex = Math.floor(index / 12) + 1; const within = index % 12;
  const state = within % 3 - 1;
  return { placementId: `c${index}`, leapIndex, emittedSites: 1,
    physicsTerms: [{ id: "uninformative", weight: 1, contribution: within % 2 }],
    contextFeatures: [{ id: "frontier-state", label: "frontier state", value: state }],
    outcomes: { shellChange: 4 * state } };
});
const contextFree = blockedCreationResponseSurrogate(contextualRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01 });
const contextAware = blockedCreationResponseSurrogate(contextualRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01, includeStructuralContext: true });
assert.ok(contextFree.heldoutSkillVersusTrainingMean < .01);
assert.ok(contextAware.heldoutSkillVersusTrainingMean > .99);
assert.equal(contextAware.features.some((feature) => feature.source === "structural-context"), true);
assert.equal(contextAware.fitUsedHeldout, false);
const stateScopeRecords = Array.from({ length: 60 }, (_, index) => {
  const leapIndex = Math.floor(index / 12) + 1; const within = index % 12;
  const local = within % 4;
  return { placementId: `l${index}`, leapIndex, emittedSites: 1,
    physicsTerms: [{ id: "uninformative", weight: 1, contribution: within % 2 }],
    contextFeatures: [
      { id: "support-sites", value: local },
      { id: "log-atoms", value: leapIndex <= 3 ? 2 + within / 12 : 20 + within / 12 },
    ], outcomes: { shellChange: 3 * local } };
});
const allState = blockedCreationResponseSurrogate(stateScopeRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01, includeStructuralContext: true });
const localState = blockedCreationResponseSurrogate(stateScopeRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01, includeStructuralContext: true,
    contextFeatureIds: LOCAL_CREATION_CONTEXT_FEATURE_IDS });
assert.equal(allState.heldoutFeatureSupportCoverage, 0);
assert.equal(localState.heldoutFeatureSupportCoverage, 1);
assert.ok(localState.heldoutSkillVersusTrainingMean > .99);
assert.ok(localState.supportedHeldoutSkillVersusTrainingMean > .99);
assert.equal(localState.contextFeatureScope, "predeclared local/intensive attachment state");
assert.deepEqual(localState.contextFeatureIds, LOCAL_CREATION_CONTEXT_FEATURE_IDS);
assert.equal(localState.interpolationReadiness.state, "full-interpolation");
assert.equal(localState.interpolationReadiness.aggregateSkillIsInterpolationTest, true);
const mixedStateRecords = stateScopeRecords.map((record, index) => index === 59 ? ({ ...record,
  contextFeatures: record.contextFeatures.map((feature) => feature.id === "support-sites"
    ? { ...feature, value: 20 } : feature) }) : record);
const mixedState = blockedCreationResponseSurrogate(mixedStateRecords, "shellChange",
  { trainingFraction: .6, minimumSamplesPerSplit: 4, ridge: .01, includeStructuralContext: true,
    contextFeatureIds: LOCAL_CREATION_CONTEXT_FEATURE_IDS });
assert.equal(mixedState.interpolationReadiness.state, "mixed-domain");
assert.equal(mixedState.interpolationReadiness.aggregateSkillIsInterpolationTest, false);
assert.equal(mixedState.interpolationReadiness.supportedSubsetSkillAvailable, true);
const horizonRecords = Array.from({ length: 72 }, (_, index) => {
  const leapIndex = Math.floor(index / 12) + 1; const local = index % 4;
  return { placementId: `h${index}`, leapIndex, emittedSites: 1,
    physicsTerms: [{ id: "score", weight: 1, contribution: index % 3 }],
    contextFeatures: [{ id: "support-sites", value: local }],
    outcomes: { shellChange: 2 * local } };
});
const horizonSweep = creationResponseHorizonSweep(horizonRecords, "shellChange",
  { minimumSamplesPerSplit: 4, ridge: .01 });
assert.equal(horizonSweep.available, true);
assert.deepEqual(horizonSweep.horizons.map((entry) => entry.count), [3, 4, 5]);
assert.deepEqual(horizonSweep.horizons.map((entry) => entry.model.trainingLeaps.length), [3, 4, 5]);
assert.equal(horizonSweep.horizons.every((entry) => entry.model.interpolationReadiness.state
  === "full-interpolation"), true);
assert.equal(horizonSweep.horizonSelectedUsingHeldout, false);
assert.equal(horizonSweep.allPredeclaredHorizonsReported, true);
const atlas = crossRunHorizonReadinessAtlas([
  { id: "run-a", material: "NaCl", receiptSha256: "a".repeat(64), inputIdentity: "nacl:same",
    creationResponseEvidence: { schema: 4, localContextHorizonSweeps: { shellChange: horizonSweep } } },
  { id: "run-b", material: "NaCl", receiptSha256: "b".repeat(64), inputIdentity: "nacl:same",
    creationResponseEvidence: { schema: 4, localContextHorizonSweeps: { shellChange: horizonSweep } } },
  { id: "run-c", material: "ice", receiptSha256: "c".repeat(64), inputIdentity: "ice:different" },
], "shellChange");
assert.equal(atlas.available, true);
assert.equal(atlas.rows.length, 2);
assert.equal(atlas.horizonDefinitions.length, 3);
assert.equal(atlas.rows.every((row) => row.sharesInputWithAnotherSavedRun), true);
assert.deepEqual(atlas.rows[0].horizons[0].trainingLeaps, [1, 2, 3]);
assert.deepEqual(atlas.rows[0].horizons[0].heldoutLeaps, [4, 5, 6]);
assert.equal(atlas.rows[0].horizons[0].fitUsedHeldout, false);
assert.equal(atlas.rows[0].horizons[0].featureSelectionUsedOutcome, false);
assert.equal(atlas.rows[0].horizons[0].features.length > 0, true);
assert.equal(atlas.placementRowsPooled, false);
assert.equal(atlas.modelsRefitAcrossRuns, false);
assert.equal(atlas.independentRunsAssumed, false);
assert.equal(atlas.targetUsed, false);
assert.equal(crossRunHorizonReadinessAtlas([], "shellChange").available, false);
console.log("materials creation-response association: passed");
