import assert from "node:assert/strict";
import { buildFiniteNetworkFirstPassage } from "./finite-network-first-passage.mjs";

function network(nodeIds, edgeRecords) {
  const nodes = nodeIds.map((id) => ({ stateId: id, stateSha256: id.repeat(64).slice(0, 64),
    shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  return {
    schema: "gcts-finite-transition-network-v1",
    nodes,
    directedEdges: edgeRecords.map(([from, to, rate], index) => ({
      key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
      logRatePerSecond: Math.log(rate), temperatureKelvin: 800,
      methodSettingsSha256: "m".repeat(64),
    })),
    hash,
  };
}

const chain = network(["a", "b", "c"], [["a", "b", 2], ["b", "c", 3]]);
const chainAudit = buildFiniteNetworkFirstPassage(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.c,
});
assert.equal(chainAudit.available, true);
assert.ok(Math.abs(chainAudit.sourceTargetHittingProbability - 1) < 1e-12);
assert.ok(Math.abs(chainAudit.sourceConditionalMeanFirstPassageSeconds - (1 / 2 + 1 / 3)) < 1e-12);
assert.ok(Math.abs(chainAudit.sourceConditionalExpectedObservedJumps - 2) < 1e-12);
assert.equal(chainAudit.numericalIdentitiesPassed, true);

const branch = network(["a", "b", "f"], [["a", "b", 2], ["a", "f", 1]]);
const branchAudit = buildFiniteNetworkFirstPassage(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.b,
});
assert.equal(branchAudit.available, true);
assert.ok(Math.abs(branchAudit.sourceTargetHittingProbability - 2 / 3) < 1e-12);
assert.ok(Math.abs(branchAudit.sourceConditionalMeanFirstPassageSeconds - 1 / 3) < 1e-12);
assert.ok(Math.abs(branchAudit.sourceConditionalExpectedObservedJumps - 1) < 1e-12);
assert.deepEqual(branchAudit.observedFailureStateSha256, [branch.hash.f]);
assert.equal(branchAudit.completeCommittorClaimed, false);

const loop = network(["a", "b", "t", "f"], [
  ["a", "b", 1], ["a", "f", 1], ["b", "a", 1], ["b", "t", 1],
]);
const loopAudit = buildFiniteNetworkFirstPassage(loop, {
  sourceStateSha256: loop.hash.a, targetStateSha256: loop.hash.t,
});
assert.ok(Math.abs(loopAudit.sourceTargetHittingProbability - 1 / 3) < 1e-12);
assert.ok(Math.abs(loopAudit.sourceConditionalMeanFirstPassageSeconds - 4 / 3) < 1e-12);
assert.ok(Math.abs(loopAudit.sourceConditionalExpectedObservedJumps - 8 / 3) < 1e-12);

const shifted = structuredClone(loop);
shifted.directedEdges.forEach((edge) => { edge.logRatePerSecond += Math.log(10); });
const shiftedAudit = buildFiniteNetworkFirstPassage(shifted, {
  sourceStateSha256: shifted.hash.a, targetStateSha256: shifted.hash.t,
});
assert.ok(Math.abs(shiftedAudit.sourceTargetHittingProbability
  - loopAudit.sourceTargetHittingProbability) < 1e-12);
assert.ok(Math.abs(shiftedAudit.sourceConditionalMeanFirstPassageSeconds
  - loopAudit.sourceConditionalMeanFirstPassageSeconds / 10) < 1e-12);

const incompatible = structuredClone(chain);
incompatible.directedEdges[1].temperatureKelvin = 900;
assert.equal(buildFiniteNetworkFirstPassage(incompatible, {
  sourceStateSha256: incompatible.hash.a, targetStateSha256: incompatible.hash.c,
}).available, false);

console.log("finite observed-network first passage: ok");
