import assert from "node:assert/strict";
import { buildFiniteNetworkConditionedHeterogeneity }
  from "./finite-network-conditioned-heterogeneity.mjs";

function network(nodeIds, records) {
  const nodes = nodeIds.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  const atomCount = Object.fromEntries(nodeIds.map((id, index) => [id, 10 + index]));
  return { nodes, hash, directedEdges: records.map(([from, to, rate, contact], index) => ({
    key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
    logRatePerSecond: Math.log(rate), temperatureKelvin: 700,
    methodSettingsSha256: "m".repeat(64), eventDirection: "attach",
    initialAtomCount: atomCount[from], finalAtomCount: atomCount[to],
    geometricPathObservable: { geometricCharacter: contact > 0 ? "contact-forming" : "contact-breaking",
      netContactDelta: contact, meanDynamicCoordinationDelta: .1 * contact,
      maximumAdjacentDisplacementAngstrom: .2 },
  })) };
}

const close = (actual, expected, tolerance = 1e-10) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);

const chain = network(["a", "b", "t"], [
  ["a", "b", 2, 1], ["b", "t", 3, 1],
]);
const chainAudit = buildFiniteNetworkConditionedHeterogeneity(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
});
assert.equal(chainAudit.available, true);
close(chainAudit.passageTime.meanScaledTime, 5 / 2);
close(chainAudit.passageTime.varianceScaledTimeSquared, 13 / 4);
close(chainAudit.passageTime.coefficientOfVariation, Math.sqrt(13) / 5);
close(chainAudit.rewardMoments.observedJumps.mean, 2);
close(chainAudit.rewardMoments.observedJumps.variance, 0);
close(chainAudit.rewardMoments.atomCountDelta.variance, 0);
assert.ok(chainAudit.edgeUse.every((edge) => edge.probabilityEverUsed === 1));
assert.ok(chainAudit.edgeUse.every((edge) => edge.expectedTraversalsConditionalOnUse === 1));
assert.equal(chainAudit.identitiesPassed, true);

const branch = network(["a", "t", "f"], [
  ["a", "t", 2, 1], ["a", "f", 1, -1],
]);
const branchAudit = buildFiniteNetworkConditionedHeterogeneity(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
});
close(branchAudit.passageTime.coefficientOfVariation, 1);
close(branchAudit.rewardMoments.observedJumps.mean, 1);
close(branchAudit.rewardMoments.observedJumps.variance, 0);
assert.equal(branchAudit.edgeUse.find((edge) => edge.toStateSha256 === branch.hash.t)
  .probabilityEverUsed, 1);
assert.equal(branchAudit.edgeUse.find((edge) => edge.toStateSha256 === branch.hash.f)
  .probabilityEverUsed, 0);
assert.equal(branchAudit.identitiesPassed, true);

const cycle = network(["a", "b", "t"], [
  ["a", "b", 1, 1], ["b", "a", 1, -1], ["b", "t", 1, 1],
]);
const cycleAudit = buildFiniteNetworkConditionedHeterogeneity(cycle, {
  sourceStateSha256: cycle.hash.a, targetStateSha256: cycle.hash.t,
});
close(cycleAudit.rewardMoments.observedJumps.mean, 4);
close(cycleAudit.rewardMoments.observedJumps.variance, 8);
close(cycleAudit.rewardMoments.atomCountDelta.variance, 0);
close(cycleAudit.rewardMoments.maximumDisplacementExposureAngstrom.mean, .8);
close(cycleAudit.rewardMoments.maximumDisplacementExposureAngstrom.variance, .32);
const returnEdge = cycleAudit.edgeUse.find((edge) =>
  edge.fromStateSha256 === cycle.hash.b && edge.toStateSha256 === cycle.hash.a);
close(returnEdge.probabilityEverUsed, .5);
close(returnEdge.expectedTraversalCount, 1);
close(returnEdge.expectedTraversalsConditionalOnUse, 2);
assert.equal(cycleAudit.optionalRecrossingEdges[0].edgeKey, returnEdge.edgeKey);
assert.equal(cycleAudit.identitiesPassed, true);
assert.equal(cycleAudit.trajectoryEnsembleSampled, false);
assert.equal(cycleAudit.rateUncertaintyPropagated, false);

console.log("finite-network conditioned heterogeneity: ok");
