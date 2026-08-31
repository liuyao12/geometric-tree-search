import assert from "node:assert/strict";
import { buildFiniteNetworkPassageControl } from "./finite-network-passage-control.mjs";

function network(nodeIds, edgeRecords) {
  const nodes = nodeIds.map((id) => ({ stateId: id, stateSha256: id.repeat(64).slice(0, 64),
    shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  return { schema: "gcts-finite-transition-network-v1", nodes, hash,
    directedEdges: edgeRecords.map(([from, to, rate, character], index) => ({
      key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
      logRatePerSecond: Math.log(rate), logRateUncertainty: .2,
      temperatureKelvin: 700, methodSettingsSha256: "m".repeat(64),
      eventDirection: "attach", initialAtomCount: 10 + index, finalAtomCount: 11 + index,
      geometricPathObservable: { geometricCharacter: character, contactReach: 1.35,
        netContactDelta: 1, meanDynamicCoordinationDelta: .2,
        maximumAdjacentDisplacementAngstrom: .4 },
    })) };
}

const chain = network(["a", "b", "t"], [
  ["a", "b", 2, "contact-forming"], ["b", "t", 3, "displacive at this contact reach"],
]);
const chainAudit = buildFiniteNetworkPassageControl(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
});
assert.equal(chainAudit.available, true);
assert.ok(Math.abs(chainAudit.edgeSensitivities[0].logPassageTimeElasticity + .6) < 1e-8);
assert.ok(Math.abs(chainAudit.edgeSensitivities[1].logPassageTimeElasticity + .4) < 1e-8);
assert.ok(chainAudit.edgeSensitivities.every((edge) =>
  Math.abs(edge.targetProbabilityElasticity) < 1e-10));
assert.equal(chainAudit.commonModeIdentitiesPassed, true);
assert.equal(chainAudit.geometryResolvedEdgeCount, 2);
assert.equal(chainAudit.causalMechanismClaimed, false);

const branch = network(["a", "t", "f"], [
  ["a", "t", 2, "contact-forming"], ["a", "f", 1, "contact-breaking"],
]);
const branchAudit = buildFiniteNetworkPassageControl(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
});
const targetEdge = branchAudit.edgeSensitivities.find((edge) =>
  edge.toStateSha256 === branch.hash.t);
const failureEdge = branchAudit.edgeSensitivities.find((edge) =>
  edge.toStateSha256 === branch.hash.f);
assert.ok(Math.abs(targetEdge.targetProbabilityElasticity - 2 / 9) < 1e-8);
assert.ok(Math.abs(failureEdge.targetProbabilityElasticity + 2 / 9) < 1e-8);
assert.ok(Math.abs(targetEdge.logPassageTimeElasticity + 2 / 3) < 1e-8);
assert.ok(Math.abs(failureEdge.logPassageTimeElasticity + 1 / 3) < 1e-8);
assert.equal(branchAudit.commonModeIdentitiesPassed, true);
assert.ok(branchAudit.independentLinearizedLogTimeSigma > 0);

assert.equal(buildFiniteNetworkPassageControl(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  logarithmicRateStep: .1,
}).available, false);

console.log("finite-network passage control: ok");
