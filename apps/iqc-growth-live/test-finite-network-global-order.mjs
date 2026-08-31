import assert from "node:assert/strict";
import { buildFiniteNetworkPopulationDynamics }
  from "./finite-network-population-dynamics.mjs";
import { buildFiniteNetworkGeometricFlux } from "./finite-network-geometric-flux.mjs";
import { buildFiniteNetworkGlobalOrder } from "./finite-network-global-order.mjs";

const descriptor = (atomCount, meanCoordination, q4, q6) => ({ atomCount,
  speciesCounts: { Na: atomCount }, contactReach: 1.35,
  medianNearestNeighborAngstrom: 2, cutoffAngstrom: 2.7,
  contactCount: Math.round(meanCoordination * atomCount / 2), meanCoordination,
  coordinationStandardDeviation: 0, minimumCoordination: meanCoordination,
  maximumCoordination: meanCoordination, sameSpeciesContactFraction: 1,
  speciesPairContactFractions: { "Na–Na": 1 }, steinhardtQ4: q4, steinhardtQ6: q6 });
const first = descriptor(4, 1, .2, .3);
const second = descriptor(4, 2, .4, .7);
const network = { nodes: [
  { stateId: "S1", stateSha256: "a", shortHash: "a" },
  { stateId: "S2", stateSha256: "b", shortHash: "b" }],
directedEdges: [
  { key: "a->b", fromStateSha256: "a", toStateSha256: "b",
    initialAtomCount: 4, finalAtomCount: 4, logRatePerSecond: Math.log(2),
    temperatureKelvin: 600, methodSettingsSha256: "method",
    initialStateGeometricDescriptor: first, finalStateGeometricDescriptor: second },
  { key: "b->a", fromStateSha256: "b", toStateSha256: "a",
    initialAtomCount: 4, finalAtomCount: 4, logRatePerSecond: 0,
    temperatureKelvin: 600, methodSettingsSha256: "method",
    initialStateGeometricDescriptor: second, finalStateGeometricDescriptor: first }],
};
const dynamics = buildFiniteNetworkPopulationDynamics(network,
  { initialStateSha256: "a", horizonMultipliers: [0, 30] });
const flux = buildFiniteNetworkGeometricFlux(network, dynamics, { horizonMultiplier: 0 });
const audit = buildFiniteNetworkGlobalOrder(network, dynamics, flux);
assert.equal(audit.available, true);
assert.equal(audit.descriptorConsistencyCertified, true);
assert.equal(audit.timeline[0].meanCoordination, 1);
assert.equal(audit.timeline[0].steinhardtQ6, .3);
assert.ok(Math.abs(audit.instantaneousOrderCurrent.meanCoordination - 1) < 1e-12);
assert.ok(Math.abs(audit.instantaneousOrderCurrent.steinhardtQ4 - .2) < 1e-12);
assert.ok(Math.abs(audit.instantaneousOrderCurrent.steinhardtQ6 - .4) < 1e-12);
assert.ok(Object.values(audit.orderCurrentIdentityResidual).every((value) =>
  Math.abs(value) < 1e-12));
assert.equal(audit.thermodynamicOrderParameterClaimed, false);

const missing = buildFiniteNetworkGlobalOrder({ ...network,
  directedEdges: [network.directedEdges[0]] }, dynamics, flux);
assert.equal(missing.available, true);

const inconsistent = buildFiniteNetworkGlobalOrder({ ...network,
  directedEdges: [...network.directedEdges, { ...network.directedEdges[0], key: "repeat",
    initialStateGeometricDescriptor: { ...first, steinhardtQ6: .9 } }] }, dynamics, flux);
assert.equal(inconsistent.available, false);
assert.match(inconsistent.reason, /inconsistent/);

console.log("finite-network global geometric order: ok");
