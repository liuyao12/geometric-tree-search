import assert from "node:assert/strict";
import { buildFiniteNetworkConditionedStructuralPath }
  from "./finite-network-conditioned-structural-path.mjs";

function descriptor(atomCount, coordination, q4, q6) {
  return { atomCount, contactReach: 1.35, medianNearestNeighborAngstrom: 1,
    contactCount: atomCount, meanCoordination: coordination,
    coordinationStandardDeviation: .2, minimumCoordination: 1,
    maximumCoordination: 4, sameSpeciesContactFraction: 1,
    steinhardtQ4: q4, steinhardtQ6: q6,
    speciesCounts: { X: atomCount }, speciesPairContactFractions: { "X–X": 1 } };
}

function network(nodeIds, records) {
  const nodes = nodeIds.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  const descriptors = Object.fromEntries(nodeIds.map((id, index) =>
    [id, descriptor(10 + index, 2 + .5 * index, .1 + .1 * index, .2 + .1 * index)]));
  return { nodes, hash, descriptors, directedEdges: records.map(([from, to, rate], index) => ({
    key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
    logRatePerSecond: Math.log(rate), temperatureKelvin: 700,
    methodSettingsSha256: "m".repeat(64), eventDirection: "attach",
    initialAtomCount: descriptors[from].atomCount, finalAtomCount: descriptors[to].atomCount,
    initialStateGeometricDescriptor: descriptors[from],
    finalStateGeometricDescriptor: descriptors[to],
    geometricPathObservable: { geometricCharacter: "contact-forming",
      netContactDelta: 1, meanDynamicCoordinationDelta: .1,
      maximumAdjacentDisplacementAngstrom: .2 },
  })) };
}

const exponential = network(["a", "t"], [["a", "t", 2]]);
const exponentialAudit = buildFiniteNetworkConditionedStructuralPath(exponential, {
  sourceStateSha256: exponential.hash.a, targetStateSha256: exponential.hash.t,
});
assert.equal(exponentialAudit.available, true);
assert.equal(exponentialAudit.timeline[0].expectedAtomCount, 10);
assert.equal(exponentialAudit.timeline[0].survivingExpectedAtomCount, 10);
assert.ok(Math.abs(exponentialAudit.medianRegion.survivingExpectedAtomCount - 10) < 1e-12);
assert.ok(exponentialAudit.timeline.at(-1).expectedAtomCount > 10.98);
assert.equal(exponentialAudit.medianRegion.dominantSurvivingState.stateId, "a");
assert.equal(exponentialAudit.identitiesPassed, true);

const chain = network(["a", "b", "t"], [["a", "b", 2], ["b", "t", 3]]);
const chainAudit = buildFiniteNetworkConditionedStructuralPath(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
});
assert.equal(chainAudit.available, true);
assert.equal(chainAudit.relevantStateCount, 3);
assert.equal(chainAudit.timeline[0].expectedSteinhardtQ6, .2);
assert.ok(chainAudit.medianRegion.survivingExpectedAtomCount > 10);
assert.ok(chainAudit.medianRegion.survivingExpectedAtomCount < 11.0000001);
assert.ok(chainAudit.timeline.at(-1).expectedSteinhardtQ6 > .399);
assert.equal(chainAudit.identitiesPassed, true);

const inconsistent = { ...chain, directedEdges: [...chain.directedEdges,
  { ...chain.directedEdges[0], key: "duplicate",
    initialStateGeometricDescriptor: { ...chain.descriptors.a, steinhardtQ6: .9 } }] };
const inconsistentAudit = buildFiniteNetworkConditionedStructuralPath(inconsistent, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
});
assert.equal(inconsistentAudit.available, false);
assert.match(inconsistentAudit.reason, /inconsistent geometric descriptors/);

console.log("finite-network conditioned structural path: ok");
