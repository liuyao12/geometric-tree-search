import assert from "node:assert/strict";
import { enumerateLocalSpeciesExchangeEvents } from "./species-exchange-events.mjs";

const site = (species, x, y = 0, z = 0) => ({ species, positionAngstrom: [x, y, z] });
const source = { sourcePlacementId: 7, clusterType: 2, ruleId: 4,
  removableAtomIds: [70, 71], removedSites: [site("Na", 0), site("Cl", 1)],
  actionSites: [site("Na", 0), site("Cl", 1), site("Cl", -.5)],
  admitted: true, targetUsed: false };
const destination = { destinationCandidateId: "attach:9", parentPlacementId: 9,
  clusterType: 5, ruleId: 12, mergedAtomIds: [90],
  emittedSites: [site("K", 2), site("Cl", 3)],
  actionSites: [site("Cl", 1.5), site("K", 2), site("Cl", 3)],
  admitted: true, targetUsed: false };

const catalog = enumerateLocalSpeciesExchangeEvents({ sources: [source],
  destinations: [destination], maximumCentroidDistanceAngstrom: 4 });
assert.equal(catalog.admitted.length, 1);
assert.equal(catalog.admitted[0].eventDirection, "exchange");
assert.equal(catalog.admitted[0].atomCountChange, 0);
assert.deepEqual(catalog.admitted[0].speciesDelta, { K: 1, Na: -1 });
assert.equal(catalog.admitted[0].sourceClusterType, "2");
assert.equal(catalog.admitted[0].destinationClusterType, "5");
assert.equal(catalog.admitted[0].sourceIndependentDestination, true);
assert.equal(catalog.barrierPrefactorAndChemicalPotentialInferred, false);
assert.equal(catalog.targetUsed, false);

const rejected = enumerateLocalSpeciesExchangeEvents({ sources: [source], destinations: [
  { ...destination, destinationCandidateId: "own-child", parentPlacementId: 7 },
  { ...destination, destinationCandidateId: "uses-source", mergedAtomIds: [70] },
  { ...destination, destinationCandidateId: "same-colors",
    emittedSites: [site("Na", 2), site("Cl", 3)] },
  { ...destination, destinationCandidateId: "count-change", emittedSites: [site("K", 2)] },
  { ...destination, destinationCandidateId: "too-far",
    emittedSites: [site("K", 20), site("Cl", 21)] },
], maximumCentroidDistanceAngstrom: 4 });
assert.equal(rejected.admitted.length, 0);
for (const reason of ["destination-depends-on-source-leaf", "destination-uses-removed-source-atom",
  "no-species-exchange", "atom-count-not-conserved", "outside-local-exchange-reach"]) {
  assert.ok(rejected.rejected.some((event) => event.reasons.includes(reason)), reason);
}

console.log("local species-exchange catalog tests passed");
