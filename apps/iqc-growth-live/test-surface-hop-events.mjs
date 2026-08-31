import assert from "node:assert/strict";
import { enumerateMassConservingSurfaceHops } from "./surface-hop-events.mjs";

const site = (species, x, y = 0, z = 0) => ({ species, positionAngstrom: [x, y, z] });
const source = { sourcePlacementId: 7, clusterType: 2, ruleId: 4,
  removableAtomIds: [70, 71], removedSites: [site("Na", 0), site("Cl", 1)],
  actionSites: [site("Na", 0), site("Cl", 1), site("Cl", -.5)],
  admitted: true, targetUsed: false };
const destination = { destinationCandidateId: "attach:9", parentPlacementId: 9,
  clusterType: 2, ruleId: 5, mergedAtomIds: [90],
  emittedSites: [site("Na", 2), site("Cl", 3)],
  actionSites: [site("Cl", 1.5), site("Na", 2), site("Cl", 3)],
  admitted: true, targetUsed: false };

const catalog = enumerateMassConservingSurfaceHops({ sources: [source],
  destinations: [destination], maximumCentroidDistanceAngstrom: 4 });
assert.equal(catalog.admitted.length, 1);
assert.equal(catalog.admitted[0].eventDirection, "hop");
assert.equal(catalog.admitted[0].atomCountChange, 0);
assert.equal(catalog.admitted[0].speciesPopulationConserved, true);
assert.equal(catalog.admitted[0].sourceIndependentDestination, true);
assert.equal(catalog.admitted[0].actionSites.length, 6);
assert.equal(catalog.targetUsed, false);
assert.equal(catalog.barrierAndPrefactorInferred, false);

const rejected = enumerateMassConservingSurfaceHops({ sources: [source], destinations: [
  { ...destination, destinationCandidateId: "own-child", parentPlacementId: 7 },
  { ...destination, destinationCandidateId: "uses-source", mergedAtomIds: [70] },
  { ...destination, destinationCandidateId: "changes-color",
    emittedSites: [site("Na", 2), site("Na", 3)] },
  { ...destination, destinationCandidateId: "too-far",
    emittedSites: [site("Na", 20), site("Cl", 21)] },
] , maximumCentroidDistanceAngstrom: 4 });
assert.equal(rejected.admitted.length, 0);
assert.ok(rejected.rejected.some((event) =>
  event.reasons.includes("destination-depends-on-source-leaf")));
assert.ok(rejected.rejected.some((event) =>
  event.reasons.includes("destination-uses-removed-source-atom")));
assert.ok(rejected.rejected.some((event) =>
  event.reasons.includes("species-population-not-conserved")));
assert.ok(rejected.rejected.some((event) =>
  event.reasons.includes("outside-local-hop-reach")));

console.log("mass-conserving surface-hop catalog tests passed");
