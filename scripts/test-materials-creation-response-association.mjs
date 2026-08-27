import assert from "node:assert/strict";
import { blockedCreationResponseValidation, buildCreationResponseAssociation,
  blockedCreationResponseSurrogate, canonicalCreationResponseDataset, creationResponseLeapProfile }
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
assert.equal(surrogate.fitUsedHeldout, false);
console.log("materials creation-response association: passed");
