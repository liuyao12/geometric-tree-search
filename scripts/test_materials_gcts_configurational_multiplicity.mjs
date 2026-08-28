import assert from "node:assert/strict";
import { continuationMultiplicityAtlas, continuationMultiplicityScore }
  from "../apps/iqc-growth-live/configurational-multiplicity.mjs";

const rules = [
  { id: 3, from: 0, to: 1, fitCount: 4, holdoutCount: 99 },
  { id: 1, from: 0, to: 2, fitCount: 4, holdoutCount: 0 },
  { id: 7, from: 1, to: 1, fitCount: 8, holdoutCount: 0 },
  { id: 8, from: 2, to: 0, fitCount: 0, holdoutCount: 100 },
];
const atlas = continuationMultiplicityAtlas(rules);
assert.equal(atlas.representedParentTypes, 2);
assert.equal(atlas.supportedRuleCount, 3);
assert.equal(atlas.byType[0].properPoseClassCount, 2);
assert.equal(atlas.byType[0].childTypeCount, 2);
assert.equal(atlas.byType[0].effectiveActionCount, 2);
assert.equal(atlas.byType[1].effectiveActionCount, 1);
assert.ok(continuationMultiplicityScore(atlas, 0, "diversify").score
  > continuationMultiplicityScore(atlas, 1, "diversify").score);
assert.ok(continuationMultiplicityScore(atlas, 1, "funnel").score
  > continuationMultiplicityScore(atlas, 0, "funnel").score);
assert.equal(continuationMultiplicityScore(atlas, 2, "diversify").deadEnd, true);
assert.equal(continuationMultiplicityScore(atlas, 2, "diversify").score, -1);
const permuted = continuationMultiplicityAtlas([...rules].reverse());
assert.deepEqual(permuted, atlas);
assert.equal(atlas.heldoutUsed, false);
assert.equal(atlas.targetUsed, false);
console.log("configurational multiplicity contract passed");
