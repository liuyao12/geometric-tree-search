import assert from "node:assert/strict";
import { buildFiniteNetworkConditionedPassage }
  from "./finite-network-conditioned-passage.mjs";

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

const chain = network(["a", "b", "t"], [
  ["a", "b", 2, 1], ["b", "t", 3, 1],
]);
const chainAudit = buildFiniteNetworkConditionedPassage(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
});
assert.equal(chainAudit.available, true);
assert.ok(Math.abs(chainAudit.stateResidence.find((state) =>
  state.stateId === "a").expectedResidenceSeconds - .5) < 1e-12);
assert.ok(Math.abs(chainAudit.stateResidence.find((state) =>
  state.stateId === "b").expectedResidenceSeconds - 1 / 3) < 1e-12);
assert.deepEqual(chainAudit.rankedEdgeTraversals.map((edge) =>
  edge.expectedTraversalCount), [1, 1]);
assert.ok(Math.abs(chainAudit.expectedTotalTraversals - 2) < 1e-12);
assert.ok(Math.abs(chainAudit.expectedCumulativeAtomCountDelta - 2) < 1e-12);
assert.ok(Math.abs(chainAudit.expectedCumulativeNetContactDelta - 2) < 1e-12);
assert.equal(chainAudit.identitiesPassed, true);
assert.equal(chainAudit.trajectoryEnsembleSampled, false);

const branch = network(["a", "t", "f"], [
  ["a", "t", 2, 1], ["a", "f", 1, -1],
]);
const branchAudit = buildFiniteNetworkConditionedPassage(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
});
assert.ok(Math.abs(branchAudit.stateResidence[0].expectedResidenceSeconds - 1 / 3) < 1e-12);
assert.ok(Math.abs(branchAudit.edgeTraversals.find((edge) =>
  edge.toStateSha256 === branch.hash.t).expectedTraversalCount - 1) < 1e-12);
assert.equal(branchAudit.edgeTraversals.find((edge) =>
  edge.toStateSha256 === branch.hash.f).expectedTraversalCount, 0);
assert.equal(branchAudit.expectedTotalTraversals, 1);
assert.equal(branchAudit.expectedTargetEntries, 1);
assert.equal(branchAudit.identitiesPassed, true);

const cycle = network(["a", "b", "t"], [
  ["a", "b", 1, 1], ["b", "a", 1, -1], ["b", "t", 1, 1],
]);
const cycleAudit = buildFiniteNetworkConditionedPassage(cycle, {
  sourceStateSha256: cycle.hash.a, targetStateSha256: cycle.hash.t,
});
const count = (from, to) => cycleAudit.edgeTraversals.find((edge) =>
  edge.fromStateSha256 === cycle.hash[from] && edge.toStateSha256 === cycle.hash[to])
  .expectedTraversalCount;
assert.ok(Math.abs(count("a", "b") - 2) < 1e-12);
assert.ok(Math.abs(count("b", "a") - 1) < 1e-12);
assert.ok(Math.abs(count("b", "t") - 1) < 1e-12);
assert.ok(Math.abs(cycleAudit.expectedTotalTraversals - 4) < 1e-12);
assert.equal(cycleAudit.identitiesPassed, true);

console.log("finite-network conditioned passage: ok");
