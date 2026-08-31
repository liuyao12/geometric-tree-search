import assert from "node:assert/strict";
import { buildFiniteNetworkPopulationDynamics }
  from "./finite-network-population-dynamics.mjs";
import { buildFiniteNetworkGeometricFlux } from "./finite-network-geometric-flux.mjs";
import { buildFiniteNetworkStructuralFlux } from "./finite-network-structural-flux.mjs";

const observable = (delta) => ({ contactReach: 1.35, contactResolved: true,
  referenceLengthAngstrom: 2, netContactDelta: delta,
  meanDynamicCoordinationDelta: .5 * delta,
  maximumAdjacentDisplacementAngstrom: .2,
  geometricCharacter: delta > 0 ? "contact-forming" : "contact-breaking" });
const network = {
  nodes: [
    { stateId: "S1", stateSha256: "a", shortHash: "a" },
    { stateId: "S2", stateSha256: "b", shortHash: "b" },
  ],
  directedEdges: [
    { key: "a->b", eventId: "ab", candidateId: "attach", eventDirection: "attach",
      fromStateSha256: "a", toStateSha256: "b", initialAtomCount: 10,
      finalAtomCount: 11, logRatePerSecond: Math.log(2), temperatureKelvin: 600,
      methodSettingsSha256: "method", geometricPathObservable: observable(1) },
    { key: "b->a", eventId: "ba", candidateId: "detach", eventDirection: "detach",
      fromStateSha256: "b", toStateSha256: "a", initialAtomCount: 11,
      finalAtomCount: 10, logRatePerSecond: 0, temperatureKelvin: 600,
      methodSettingsSha256: "method", geometricPathObservable: observable(-1) },
  ],
  pairedEdges: [{ pairAudit: { sameGeometricContactDefinition: true,
    geometricPathObservableClosurePassed: true } }],
};
const dynamics = buildFiniteNetworkPopulationDynamics(network, {
  initialStateSha256: "a", horizonMultipliers: [0, 30],
});
const initialGeometricFlux = buildFiniteNetworkGeometricFlux(network, dynamics,
  { horizonMultiplier: 0 });
const initial = buildFiniteNetworkStructuralFlux(network, dynamics, initialGeometricFlux);
assert.equal(initial.available, true);
assert.equal(initial.geometryObservedActivityFraction, 1);
assert.equal(initial.contactResolvedActivityFraction, 1);
assert.ok(Math.abs(initial.observedNetContactDriftPerObservedTimescale - 1) < 1e-12);
assert.ok(Math.abs(initial.observedNetContactDriftPerSecond - 2) < 1e-12);
assert.ok(Math.abs(initial.observedMeanDynamicCoordinationDriftPerObservedTimescale - .5) < 1e-12);
assert.ok(Math.abs(initial.expectedMaximumAdjacentDisplacementActivityAngstromPerObservedTimescale
  - .2) < 1e-12);
assert.equal(initial.dominantResolvedGeometricCharacter, "contact-forming");
assert.equal(initial.inversePairGeometryAudit.everyComparablePairClosed, true);
assert.equal(initial.chemicalBondClaimed, false);

const lateGeometricFlux = buildFiniteNetworkGeometricFlux(network, dynamics,
  { horizonMultiplier: 30 });
const late = buildFiniteNetworkStructuralFlux(network, dynamics, lateGeometricFlux);
assert.ok(Math.abs(late.observedNetContactDriftPerObservedTimescale) < 1e-10);
assert.ok(late.characterActivityFractionOfResolved["contact-forming"] > .49);
assert.ok(late.characterActivityFractionOfResolved["contact-breaking"] > .49);

const mixedReach = buildFiniteNetworkStructuralFlux({ ...network,
  directedEdges: [network.directedEdges[0], { ...network.directedEdges[1],
    geometricPathObservable: { ...observable(-1), contactReach: 1.6 } }] },
  dynamics, lateGeometricFlux);
assert.equal(mixedReach.available, false);
assert.match(mixedReach.reason, /different contact-reach/);

console.log("finite observed-network structural flux: ok");
