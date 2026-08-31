import assert from "node:assert/strict";
import { buildGeometricStateDescriptor }
  from "./geometric-state-descriptor.mjs";
import { buildFiniteNetworkConditionedScatteringPath }
  from "./finite-network-conditioned-scattering-path.mjs";

const pointSets = {
  a: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
  b: [[0, 0, 0], [1, 0, 0], [0, 1.1, 0], [0, 0, 1], [1, 1, .3]],
  c: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1.2], [1, 1, 0], [.3, 1, 1]],
  t: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1]],
};

function makeDescriptor(id) {
  return buildGeometricStateDescriptor(pointSets[id].map((positionAngstrom) => ({
    species: "X", positionAngstrom,
  })), { contactReach: 1.4 });
}

function network() {
  const ids = ["a", "b", "c", "t"];
  const nodes = ids.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  const descriptors = Object.fromEntries(ids.map((id) => [id, makeDescriptor(id)]));
  const records = [["a", "b", 2], ["a", "c", 2], ["b", "t", 1], ["c", "t", 1]];
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

const branching = network();
const audit = buildFiniteNetworkConditionedScatteringPath(branching, {
  sourceStateSha256: branching.hash.a, targetStateSha256: branching.hash.t,
});
assert.equal(audit.available, true);
assert.equal(audit.qTimesMedianNearestNeighbor.length, 24);
assert.equal(audit.sourceIntensity.length, 24);
assert.equal(audit.targetIntensity.length, 24);
assert.equal(audit.contrastIndices.length, 4);
assert.ok(audit.sourceTargetRmsDifference > 0);
assert.equal(audit.initialMeanResidual, 0);
assert.equal(audit.initialVarianceResidual, 0);
assert.ok(audit.timeline.some((sample) => sample.surviving?.rmsStandardDeviation > 0));
assert.ok(audit.peakSpectralDispersion.surviving.rmsStandardDeviation > 0);
assert.equal(audit.identitiesPassed, true);
assert.equal(audit.targetUsed, false);
assert.equal(audit.trajectorySampled, false);
assert.equal(audit.experimentalIntensityClaimed, false);
assert.equal(audit.qDependentFormFactorsUsed, false);

const missingDescriptor = { ...branching.descriptors.b };
delete missingDescriptor.dimensionlessPowderScattering;
const missing = { ...branching, directedEdges: branching.directedEdges.map((edge, index) =>
  index === 0 ? { ...edge, finalStateGeometricDescriptor: missingDescriptor } : edge) };
const missingAudit = buildFiniteNetworkConditionedScatteringPath(missing, {
  sourceStateSha256: branching.hash.a, targetStateSha256: branching.hash.t,
});
assert.equal(missingAudit.available, false);
assert.match(missingAudit.reason, /lack a finite powder signature/);

const altered = structuredClone(branching.descriptors.a);
altered.dimensionlessPowderScattering.unitWeightIntensity[3] += .01;
const inconsistent = { ...branching, directedEdges: [...branching.directedEdges,
  { ...branching.directedEdges[0], key: "duplicate",
    initialStateGeometricDescriptor: altered }] };
const inconsistentAudit = buildFiniteNetworkConditionedScatteringPath(inconsistent, {
  sourceStateSha256: branching.hash.a, targetStateSha256: branching.hash.t,
});
assert.equal(inconsistentAudit.available, false);
assert.match(inconsistentAudit.reason, /inconsistent powder signatures/);

console.log("finite-network conditioned scattering path: ok");
