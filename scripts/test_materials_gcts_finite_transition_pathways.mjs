import assert from "node:assert/strict";
import { auditCompetingObservedTransitionPaths, selectObservedTransitionPath }
  from "../apps/iqc-growth-live/finite-transition-pathways.mjs";

const edge = (from, to, logRate, barrier = 1, omega = .1) => ({
  key: `${from}->${to}`, fromStateSha256: from, toStateSha256: to,
  logRatePerSecond: logRate, logRateUncertainty: .1,
  barrierElectronVolt: barrier, barrierUncertaintyElectronVolt: .02,
  grandPotentialDeltaElectronVolt: omega,
  grandPotentialDeltaUncertaintyElectronVolt: .01,
  temperatureKelvin: 300, methodSettingsSha256: "method",
  freeEnergySettingsSha256: "free", chemicalPotentialSettingsSha256: "mu",
});
const network = {
  schema: "gcts-finite-transition-network-v1",
  nodes: ["A", "B", "C", "D"].map((stateSha256, index) =>
    ({ stateSha256, stateId: `S${index + 1}` })),
  directedEdges: [edge("A", "D", -8, 1.4, .3), edge("A", "B", -2, .4, .1),
    edge("B", "D", -3, .5, .2), edge("A", "C", -4, .7, .15),
    edge("C", "D", -4, .7, .15)],
};

const primary = selectObservedTransitionPath(network, "A", "D");
assert.deepEqual(primary.stateHashes, ["A", "B", "D"]);
assert.equal(primary.bottleneckEdgeKey, "B->D");
assert.equal(primary.bottleneckLogRatePerSecond, -3);
assert.ok(Math.abs(primary.grandPotentialDeltaElectronVolt - .3) < 1e-12);
assert.ok(primary.conditionalSerialWaitingTimeSeconds > Math.exp(3));
assert.equal(primary.targetUsed, false);
assert.equal(primary.kineticConditionsComparable, true);

const audit = auditCompetingObservedTransitionPaths(network, "A", "D");
assert.deepEqual(audit.competing.stateHashes, ["A", "C", "D"]);
assert.equal(audit.bottleneckLogRateSeparation, 1);
assert.equal(audit.meanFirstPassageTimeClaimed, false);
assert.equal(audit.globalFastestPathCertified, false);
assert.equal(audit.distinctCompetingPathAvailable, true);
assert.equal(audit.competingPathComparisonEligible, true);

const reversedInput = { ...network, nodes: [...network.nodes].reverse(),
  directedEdges: [...network.directedEdges].reverse() };
assert.deepEqual(selectObservedTransitionPath(reversedInput, "A", "D").edgeKeys,
  primary.edgeKeys);
assert.equal(selectObservedTransitionPath(network, "D", "A"), null);
assert.equal(selectObservedTransitionPath(network, "missing", "A"), null);

const weakened = { ...network, directedEdges: network.directedEdges.map((entry) =>
  entry.key === "B->D" ? { ...entry, logRatePerSecond: -9 } : entry) };
assert.deepEqual(selectObservedTransitionPath(weakened, "A", "D").stateHashes,
  ["A", "C", "D"]);

console.log("finite observed transition pathways: passed");
