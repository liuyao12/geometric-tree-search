import assert from "node:assert/strict";
import { buildFiniteNetworkFirstPassageUncertainty }
  from "./finite-network-first-passage-uncertainty.mjs";

function network(edgeRecords) {
  const nodeIds = [...new Set(edgeRecords.flatMap(([from, to]) => [from, to]))];
  const nodes = nodeIds.map((id) => ({ stateId: id, stateSha256: id.repeat(64).slice(0, 64),
    shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  return { schema: "gcts-finite-transition-network-v1", nodes, hash,
    directedEdges: edgeRecords.map(([from, to, rate, sigma], index) => ({
      key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
      logRatePerSecond: Math.log(rate), logRateUncertainty: sigma,
      temperatureKelvin: 700, methodSettingsSha256: "m".repeat(64),
    })) };
}

const certain = network([["a", "b", 2, 0], ["b", "t", 3, 0]]);
const certainAudit = buildFiniteNetworkFirstPassageUncertainty(certain, {
  sourceStateSha256: certain.hash.a, targetStateSha256: certain.hash.t, sampleCount: 32,
});
assert.equal(certainAudit.available, true);
assert.equal(certainAudit.sourceTargetHittingProbability.q05, 1);
assert.equal(certainAudit.sourceTargetHittingProbability.q95, 1);
assert.ok(Math.abs(certainAudit.sourceConditionalMeanFirstPassageLogSeconds.q05
  - certainAudit.sourceConditionalMeanFirstPassageLogSeconds.q95) < 1e-12);
assert.equal(certainAudit.allSampleIdentitiesPassed, true);

const branch = network([["a", "t", 2, .55], ["a", "f", 1, .55]]);
const options = { sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  sampleCount: 64 };
const branchAudit = buildFiniteNetworkFirstPassageUncertainty(branch, options);
const repeated = buildFiniteNetworkFirstPassageUncertainty(branch, options);
assert.deepEqual(branchAudit, repeated);
assert.equal(branchAudit.available, true);
assert.ok(branchAudit.sourceTargetHittingProbability.q05
  < branchAudit.nominal.sourceTargetHittingProbability);
assert.ok(branchAudit.sourceTargetHittingProbability.q95
  > branchAudit.nominal.sourceTargetHittingProbability);
assert.ok(branchAudit.sourceConditionalMeanFirstPassageTimeRatioQ95ToQ05 > 1);
assert.equal(branchAudit.nominalValuesInsideQ05Q95, true);
assert.equal(branchAudit.confidenceIntervalClaimed, false);
assert.equal(branchAudit.edgeTopologyChanged, false);

const incomplete = structuredClone(branch);
incomplete.directedEdges[0].logRateUncertainty = null;
const incompleteAudit = buildFiniteNetworkFirstPassageUncertainty(incomplete, options);
assert.equal(incompleteAudit.available, false);
assert.equal(incompleteAudit.uncertaintyCompleteEdgeCount, 1);

assert.equal(buildFiniteNetworkFirstPassageUncertainty(branch, { ...options,
  sampleCount: 15 }).available, false);

console.log("finite first-passage uncertainty ensemble: ok");
