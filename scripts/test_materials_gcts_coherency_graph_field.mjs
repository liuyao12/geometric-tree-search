import assert from "node:assert/strict";
import { screenedCoherencyGraphField } from "../apps/iqc-growth-live/coherency-graph-field.mjs";

const adjacency = { 1: [2], 2: [1, 3], 3: [2, 4], 4: [3] };
const sources = [
  { id: 1, mismatch: .2, axis: [1, 0, 0] },
  { id: 3, mismatch: .8, axis: [0, 1, 0] },
  { id: 4, mismatch: .5, axis: [1, 0, 0] },
];
const field = screenedCoherencyGraphField({ adjacency, sources, startIds: [1],
  candidateAxis: [1, 0, 0], screeningLengthHops: 2 });
assert.equal(field.connectedGraphNodes, 4);
assert.equal(field.sourceMarks, 3);
assert.equal(field.farthestGraphHop, 3);
assert.ok(field.inheritedMismatch > .2 && field.inheritedMismatch < .8);
assert.ok(field.orientationAgreement > .5 && field.orientationAgreement <= 1);
assert.ok(field.effectiveSourceCount > 1 && field.effectiveSourceCount < 3);
assert.deepEqual(field.shells.map((shell) => shell.graphNodes), [1, 1, 1, 1]);
assert.equal(field.targetUsed, false);

const permuted = screenedCoherencyGraphField({
  adjacency: { 4: [3], 2: [3, 1], 1: [2], 3: [4, 2] },
  sources: [...sources].reverse(), startIds: [1], candidateAxis: [1, 0, 0], screeningLengthHops: 2,
});
assert.equal(permuted.inheritedMismatch, field.inheritedMismatch);
assert.equal(permuted.orientationAgreement, field.orientationAgreement);
assert.deepEqual(permuted.shells, field.shells);
assert.throws(() => screenedCoherencyGraphField({ adjacency, sources, startIds: [1],
  candidateAxis: [1, 0, 0], screeningLengthHops: 0 }), /screening length/);
console.log("screened coherency graph field contract passed");
