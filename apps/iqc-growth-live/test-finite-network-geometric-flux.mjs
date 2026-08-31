import assert from "node:assert/strict";
import { buildFiniteNetworkPopulationDynamics }
  from "./finite-network-population-dynamics.mjs";
import { buildFiniteNetworkGeometricFlux } from "./finite-network-geometric-flux.mjs";

const network = {
  nodes: [
    { stateId: "S1", stateSha256: "a", shortHash: "a" },
    { stateId: "S2", stateSha256: "b", shortHash: "b" },
  ],
  directedEdges: [
    { key: "a->b", eventId: "ab", candidateId: "attach", eventDirection: "attach",
      fromStateSha256: "a", toStateSha256: "b", initialAtomCount: 10,
      finalAtomCount: 11, logRatePerSecond: Math.log(2), temperatureKelvin: 600,
      methodSettingsSha256: "method" },
    { key: "b->a", eventId: "ba", candidateId: "detach", eventDirection: "detach",
      fromStateSha256: "b", toStateSha256: "a", initialAtomCount: 11,
      finalAtomCount: 10, logRatePerSecond: 0, temperatureKelvin: 600,
      methodSettingsSha256: "method" },
  ],
};
const dynamics = buildFiniteNetworkPopulationDynamics(network, {
  initialStateSha256: "a", horizonMultipliers: [0, 1, 30],
});
const initialFlux = buildFiniteNetworkGeometricFlux(network, dynamics,
  { horizonMultiplier: 0 });
assert.equal(initialFlux.available, true);
assert.equal(initialFlux.directedFluxes.length, 2);
assert.equal(initialFlux.netEdgeCurrents.length, 1);
assert.ok(Math.abs(initialFlux.expectedAtomDriftPerObservedTimescale - 1) < 1e-12);
assert.ok(Math.abs(initialFlux.expectedAtomDriftPerSecond - 2) < 1e-12);
assert.ok(Math.abs(initialFlux.probabilityConservationResidualPerObservedTimescale) < 1e-12);
assert.ok(Math.abs(initialFlux.expectedAtomDriftIdentityResidualPerObservedTimescale) < 1e-12);
assert.equal(initialFlux.activityByPopulationClass.growth, 1);
assert.equal(initialFlux.equilibriumClaimed, false);
assert.equal(initialFlux.macroscopicInterfaceVelocityClaimed, false);

const lateFlux = buildFiniteNetworkGeometricFlux(network, dynamics,
  { horizonMultiplier: 30 });
assert.ok(Math.abs(lateFlux.expectedAtomDriftPerObservedTimescale) < 1e-10);
assert.ok(Math.abs(lateFlux.netEdgeCurrents[0].netProbabilityCurrentPerObservedTimescale) < 1e-10);
assert.ok(lateFlux.totalTransitionActivityPerObservedTimescale > 0.6);

const unavailable = buildFiniteNetworkGeometricFlux(network, { available: false,
  reason: "missing rates" });
assert.equal(unavailable.available, false);
assert.match(unavailable.reason, /missing rates/);

console.log("finite observed-network geometric flux: ok");
