import assert from "node:assert/strict";
import { buildFiniteNetworkRateIntervention }
  from "./finite-network-rate-intervention.mjs";

function network(nodeIds, edgeRecords) {
  const nodes = nodeIds.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  return { nodes, hash, directedEdges: edgeRecords.map(([from, to, rate, character], index) => ({
    key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
    logRatePerSecond: Math.log(rate), logRateUncertainty: .2,
    temperatureKelvin: 700, methodSettingsSha256: "m".repeat(64),
    eventDirection: "attach", initialAtomCount: 10, finalAtomCount: 11,
    geometricPathObservable: { geometricCharacter: character, contactReach: 1.35,
      netContactDelta: 1, meanDynamicCoordinationDelta: .2,
      maximumAdjacentDisplacementAngstrom: .4 },
  })) };
}

const chain = network(["a", "b", "t"], [
  ["a", "b", 2, "contact-forming"], ["b", "t", 3, "displacive"],
]);
const original = JSON.stringify(chain);
const chainAudit = buildFiniteNetworkRateIntervention(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
  edgeKey: "edge-0", rateMultiplier: 2,
});
assert.equal(chainAudit.available, true);
assert.equal(chainAudit.selectedResponse.rateMultiplier, 2);
assert.ok(Math.abs(chainAudit.selectedResponse.exactConditionalPassageTimeRatio - .7) < 1e-10);
assert.ok(Math.abs(chainAudit.selectedResponse.targetHittingProbabilityChange) < 1e-12);
assert.equal(chainAudit.selectedResponse.exactExpectedJumpRatio, 1);
assert.ok(Math.abs(chainAudit.localElasticity.logPassageTimeElasticity + .6) < 1e-8);
assert.equal(JSON.stringify(chain), original);
assert.equal(chainAudit.networkMutated, false);
assert.equal(chainAudit.geometryChanged, false);
assert.equal(chainAudit.physicalInterventionClaimed, false);

const branch = network(["a", "t", "f"], [
  ["a", "t", 2, "contact-forming"], ["a", "f", 1, "contact-breaking"],
]);
const branchAudit = buildFiniteNetworkRateIntervention(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  edgeKey: "edge-0", rateMultiplier: 2,
});
assert.ok(Math.abs(branchAudit.selectedResponse.targetHittingProbability - .8) < 1e-12);
assert.ok(Math.abs(branchAudit.selectedResponse.targetHittingProbabilityChange - 2 / 15) < 1e-12);
assert.ok(Math.abs(branchAudit.selectedResponse.exactConditionalPassageTimeRatio - .6) < 1e-12);
assert.ok(branchAudit.selectedResponse.nonlinearLogTimeDepartureFromLocalTangent !== 0);
assert.deepEqual(branchAudit.responseMultipliers, [.25, .5, 1, 2, 4]);

assert.equal(buildFiniteNetworkRateIntervention(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  edgeKey: "missing", rateMultiplier: 2,
}).available, false);
assert.equal(buildFiniteNetworkRateIntervention(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  edgeKey: "edge-0", rateMultiplier: 100,
}).available, false);

console.log("finite-network rate intervention: ok");
