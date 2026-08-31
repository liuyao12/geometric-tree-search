import assert from "node:assert/strict";
import { buildFiniteNetworkConditionedArrival }
  from "./finite-network-conditioned-arrival.mjs";

function network(nodeIds, records) {
  const nodes = nodeIds.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  const atomCount = Object.fromEntries(nodeIds.map((id, index) => [id, 10 + index]));
  return { nodes, hash, directedEdges: records.map(([from, to, rate], index) => ({
    key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
    logRatePerSecond: Math.log(rate), temperatureKelvin: 700,
    methodSettingsSha256: "m".repeat(64), eventDirection: "attach",
    initialAtomCount: atomCount[from], finalAtomCount: atomCount[to],
    geometricPathObservable: { geometricCharacter: "contact-forming",
      netContactDelta: 1, meanDynamicCoordinationDelta: .1,
      maximumAdjacentDisplacementAngstrom: .2 },
  })) };
}

const close = (actual, expected, tolerance = 2e-9) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);

const exponential = network(["a", "t"], [["a", "t", 2]]);
const exponentialAudit = buildFiniteNetworkConditionedArrival(exponential, {
  sourceStateSha256: exponential.hash.a, targetStateSha256: exponential.hash.t,
});
assert.equal(exponentialAudit.available, true);
close(exponentialAudit.conditionalTimeCoefficientOfVariation, 1);
close(exponentialAudit.quantiles.q05.relativeToConditionalMean, -Math.log(.95));
close(exponentialAudit.quantiles.median.relativeToConditionalMean, Math.log(2));
close(exponentialAudit.quantiles.q95.relativeToConditionalMean, -Math.log(.05));
close(exponentialAudit.timeline[0].cumulativeArrivalProbability, 0);
assert.equal(exponentialAudit.monotonicArrivalPassed, true);
assert.equal(exponentialAudit.identitiesPassed, true);

const branch = network(["a", "t", "f"], [
  ["a", "t", 2], ["a", "f", 1],
]);
const branchAudit = buildFiniteNetworkConditionedArrival(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
});
close(branchAudit.quantiles.median.seconds, Math.log(2) / 3);
close(branchAudit.quantiles.q95.seconds, -Math.log(.05) / 3);
assert.equal(branchAudit.identitiesPassed, true);

const chain = network(["a", "b", "t"], [
  ["a", "b", 2], ["b", "t", 3],
]);
const chainAudit = buildFiniteNetworkConditionedArrival(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
});
const sampleAtOneSecond = chainAudit.timeline.reduce((best, sample) =>
  Math.abs((sample.elapsedSeconds ?? Infinity) - 1) < Math.abs((best.elapsedSeconds ?? Infinity) - 1)
    ? sample : best);
const exactAtSample = 1 - (3 * Math.exp(-2 * sampleAtOneSecond.elapsedSeconds)
  - 2 * Math.exp(-3 * sampleAtOneSecond.elapsedSeconds));
close(sampleAtOneSecond.cumulativeArrivalProbability, exactAtSample, 2e-8);
assert.ok(chainAudit.quantiles.q05.relativeToConditionalMean
  < chainAudit.quantiles.median.relativeToConditionalMean);
assert.ok(chainAudit.quantiles.median.relativeToConditionalMean
  < chainAudit.quantiles.q95.relativeToConditionalMean);
assert.equal(chainAudit.identitiesPassed, true);
assert.equal(chainAudit.trajectoryEnsembleSampled, false);
assert.equal(chainAudit.rateUncertaintyPropagated, false);

console.log("finite-network conditioned arrival: ok");
