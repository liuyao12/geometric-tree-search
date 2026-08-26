import assert from "node:assert/strict";
import { buildSiteCreationResponse } from "../apps/iqc-growth-live/site-creation-response.js";

const creation = {
  centerPositionAngstrom: [0, 0, 0], reachAngstrom: 2,
  neighbors: [
    { siteId: 1, species: "Na", vectorAngstrom: [1, 0, 0] },
    { siteId: 2, species: "Cl", vectorAngstrom: [0, 1, 0] },
    { siteId: 3, species: "Cl", vectorAngstrom: [0, 0, 1] },
    { siteId: 4, species: "Na", vectorAngstrom: [-1, 0, 0] },
  ],
};
const current = {
  centerPositionAngstrom: [.1, 0, 0],
  neighbors: [
    { siteId: 1, species: "Na", vectorAngstrom: [1.1, 0, 0] },
    { siteId: 2, species: "Cl", vectorAngstrom: [0, 1.1, 0] },
    { siteId: 3, species: "Cl", vectorAngstrom: [0, 0, 1.1] },
    { siteId: 5, species: "Yb", vectorAngstrom: [-1, 0, 0] },
  ],
};
const audit = buildSiteCreationResponse(creation, current);
assert.equal(audit.available, true);
assert.equal(audit.persistentNeighborCount, 3);
assert.equal(audit.lostNeighborCount, 1);
assert.equal(audit.gainedNeighborCount, 1);
assert.equal(audit.centerDisplacementAngstrom, .1);
assert.equal(audit.radialRmsAngstrom, .1);
assert.equal(audit.affineResolved, true);
assert.equal(audit.equivalentShearStrain, 0);
assert.equal(audit.localVolumeChangeFraction, .331);
assert.equal(audit.targetUsed, false);
assert.equal(audit.physicalDynamicsIntegrated, false);
assert.equal(buildSiteCreationResponse(null, current).available, false);
assert.throws(() => buildSiteCreationResponse({ ...creation, neighbors: [{ siteId: 1 }] }, current), /neighbor records/);

const planar = buildSiteCreationResponse({ ...creation, neighbors: creation.neighbors.slice(0, 3).map((entry) =>
  ({ ...entry, vectorAngstrom: [entry.vectorAngstrom[0], entry.vectorAngstrom[1], 0] })) }, {
  ...current, neighbors: current.neighbors.slice(0, 3).map((entry) =>
    ({ ...entry, vectorAngstrom: [entry.vectorAngstrom[0], entry.vectorAngstrom[1], 0] })),
});
assert.equal(planar.affineResolved, false);
assert.equal(planar.equivalentShearStrain, null);
console.log("materials site creation response: passed");
