import assert from "node:assert/strict";
import { buildFiniteNetworkConditionedStructuralDispersion }
  from "./finite-network-conditioned-structural-dispersion.mjs";

function descriptor(atomCount, coordination, q4, q6) {
  return { atomCount, contactReach: 1.35, medianNearestNeighborAngstrom: 1,
    contactCount: atomCount, meanCoordination: coordination,
    coordinationStandardDeviation: .2, minimumCoordination: 1,
    maximumCoordination: 6, sameSpeciesContactFraction: 1,
    steinhardtQ4: q4, steinhardtQ6: q6,
    speciesCounts: { X: atomCount }, speciesPairContactFractions: { "X–X": 1 } };
}

function network(nodeIds, records, descriptorValues) {
  const nodes = nodeIds.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  const descriptors = Object.fromEntries(nodeIds.map((id, index) =>
    [id, descriptor(...descriptorValues[index])]));
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

const branching = network(["a", "b", "c", "t"], [
  ["a", "b", 2], ["a", "c", 2], ["b", "t", 1], ["c", "t", 1],
], [
  [10, 2, .10, .20], [12, 3, .25, .42],
  [14, 4, .45, .65], [16, 5, .60, .80],
]);
const audit = buildFiniteNetworkConditionedStructuralDispersion(branching, {
  sourceStateSha256: branching.hash.a, targetStateSha256: branching.hash.t,
});
assert.equal(audit.available, true);
assert.equal(audit.initialVarianceResidual, 0);
assert.ok(audit.timeline.some((sample) =>
  sample.surviving?.fields.atomCount.standardDeviation > 0));
assert.ok(audit.timeline.some((sample) =>
  sample.targetInclusive.fields.steinhardtQ6.standardDeviation > 0));
assert.ok(audit.peakSurvivorDiversity.surviving.effectiveStateCount > 1);
assert.ok(audit.medianRegion.surviving.fields.atomCount.q10
  <= audit.medianRegion.surviving.fields.atomCount.median);
assert.ok(audit.medianRegion.surviving.fields.atomCount.median
  <= audit.medianRegion.surviving.fields.atomCount.q90);
assert.ok(audit.maximumMeanConsistencyResidual < 1e-12);
assert.equal(audit.identitiesPassed, true);
assert.equal(audit.targetUsed, false);
assert.equal(audit.trajectorySampled, false);
assert.equal(audit.thermalFluctuationClaimed, false);

const single = network(["a", "t"], [["a", "t", 2]], [
  [10, 2, .1, .2], [11, 2.5, .2, .3],
]);
const singleAudit = buildFiniteNetworkConditionedStructuralDispersion(single, {
  sourceStateSha256: single.hash.a, targetStateSha256: single.hash.t,
});
assert.equal(singleAudit.available, true);
assert.equal(singleAudit.medianRegion.surviving.fields.atomCount.standardDeviation, 0);
assert.equal(singleAudit.medianRegion.surviving.effectiveStateCount, 1);

const inconsistent = { ...branching, directedEdges: [...branching.directedEdges,
  { ...branching.directedEdges[0], key: "duplicate",
    initialStateGeometricDescriptor: { ...branching.descriptors.a, steinhardtQ6: .9 } }] };
const inconsistentAudit = buildFiniteNetworkConditionedStructuralDispersion(inconsistent, {
  sourceStateSha256: branching.hash.a, targetStateSha256: branching.hash.t,
});
assert.equal(inconsistentAudit.available, false);
assert.match(inconsistentAudit.reason, /inconsistent geometric descriptors/);

console.log("finite-network conditioned structural dispersion: ok");
