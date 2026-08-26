import assert from "node:assert/strict";
import { appendSiteStructuralHistory, summarizeSiteStructuralHistory }
  from "../apps/iqc-growth-live/site-structural-history.js";

const base = { label: "attachment", persistentNeighborCount: 6, lostNeighborCount: 0,
  gainedNeighborCount: 0, centerDisplacementAngstrom: 0, radialRmsAngstrom: 0,
  rootD2MinAngstrom: 0, equivalentShearStrain: 0, localVolumeChangeFraction: 0 };
let history = appendSiteStructuralHistory([], { ...base, leapIndex: 1 });
history = appendSiteStructuralHistory(history, { ...base, leapIndex: 2 });
assert.equal(history.length, 1, "unchanged affected states should not inflate the history");
history = appendSiteStructuralHistory(history, { ...base, leapIndex: 3, gainedNeighborCount: 2,
  radialRmsAngstrom: .04, rootD2MinAngstrom: .02 });
history = appendSiteStructuralHistory(history, { ...base, leapIndex: 4, gainedNeighborCount: 3,
  radialRmsAngstrom: .06, rootD2MinAngstrom: .03 });
assert.deepEqual(history.map((entry) => entry.leapIndex), [1, 3, 4]);
assert.equal(history.every((entry) => !entry.targetUsed && !entry.physicalTimeModeled), true);
const summary = summarizeSiteStructuralHistory(history);
assert.equal(summary.available, true);
assert.equal(summary.records, 3);
assert.equal(summary.shellChangedLeaps, 2);
assert.equal(summary.maximumGainedNeighbors, 3);
assert.equal(summary.maximumRadialRmsAngstrom, .06);
assert.equal(summarizeSiteStructuralHistory([]).available, false);
assert.throws(() => appendSiteStructuralHistory([], { leapIndex: 0 }, 24), /ordered finite leap/);
let bounded = [];
for (let leap = 1; leap <= 8; leap++) bounded = appendSiteStructuralHistory(bounded,
  { ...base, leapIndex: leap, gainedNeighborCount: leap }, 4);
assert.deepEqual(bounded.map((entry) => entry.leapIndex), [5, 6, 7, 8]);
console.log("materials site structural history: passed");
