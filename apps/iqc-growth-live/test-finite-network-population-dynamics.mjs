import assert from "node:assert/strict";
import { buildFiniteNetworkPopulationDynamics }
  from "./finite-network-population-dynamics.mjs";

const network = {
  nodes: [
    { stateId: "S1", stateSha256: "a", shortHash: "a" },
    { stateId: "S2", stateSha256: "b", shortHash: "b" },
  ],
  directedEdges: [
    { fromStateSha256: "a", toStateSha256: "b", initialAtomCount: 10,
      finalAtomCount: 11, logRatePerSecond: Math.log(2), temperatureKelvin: 600,
      methodSettingsSha256: "method" },
    { fromStateSha256: "b", toStateSha256: "a", initialAtomCount: 11,
      finalAtomCount: 10, logRatePerSecond: 0, temperatureKelvin: 600,
      methodSettingsSha256: "method" },
  ],
};

const audit = buildFiniteNetworkPopulationDynamics(network, {
  initialStateSha256: "a", horizonMultipliers: [0, 1, 30],
});
assert.equal(audit.available, true);
assert.equal(audit.probabilityConserved, true);
assert.equal(audit.nonnegativeProbabilities, true);
assert.equal(audit.timeline[0].expectedAtomCount, 10);
assert.ok(Math.abs(audit.timeline.at(-1).stateProbabilities[0].probability - 1 / 3) < 1e-10);
assert.ok(Math.abs(audit.timeline.at(-1).stateProbabilities[1].probability - 2 / 3) < 1e-10);
assert.ok(Math.abs(audit.timeline.at(-1).expectedAtomCount - 10 - 2 / 3) < 1e-10);
assert.equal(audit.equilibriumClaimed, false);
assert.equal(audit.mechanismCatalogComplete, false);
assert.equal(audit.targetUsed, false);

const absorbing = buildFiniteNetworkPopulationDynamics({ ...network,
  directedEdges: [network.directedEdges[0]] }, { initialStateSha256: "a",
  horizonMultipliers: [0, 30] });
assert.equal(absorbing.available, true);
assert.equal(absorbing.observedDeadEndStateCount, 1);
assert.ok(absorbing.timeline.at(-1).stateProbabilities[1].probability > 0.9999999999);

const mixedTemperature = buildFiniteNetworkPopulationDynamics({ ...network,
  directedEdges: [network.directedEdges[0],
    { ...network.directedEdges[1], temperatureKelvin: 601 }] });
assert.equal(mixedTemperature.available, false);
assert.match(mixedTemperature.reason, /one temperature/);

const inconsistentCounts = buildFiniteNetworkPopulationDynamics({ ...network,
  directedEdges: [network.directedEdges[0],
    { ...network.directedEdges[1], finalAtomCount: 12 }] });
assert.equal(inconsistentCounts.available, false);
assert.match(inconsistentCounts.reason, /inconsistent/);

console.log("finite observed-network population dynamics: ok");
