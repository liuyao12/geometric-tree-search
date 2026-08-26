import assert from "node:assert/strict";
import { buildSiteProvenance } from "../apps/iqc-growth-live/site-provenance.js";

const atoms = [
  { id: 1, species: "Na", p: [0, 0, 0], seed: true, referenceIndex: 7, clusterIds: [1], nucleusIds: [1] },
  { id: 2, species: "Cl", p: [1, 0, 0], seed: false, createdByClusterId: 2, clusterIds: [1, 2], nucleusIds: [1] },
  { id: 3, species: "Na", p: [0, 2, 0], seed: false, clusterIds: [2], nucleusIds: [1, 2], interfaceContact: true },
];
const placements = [
  { id: 1, type: 0, parentId: null, ruleId: null, depth: 0, nucleusId: 1, seedNucleus: true, atomIds: [1, 2] },
  { id: 2, type: 1, parentId: 1, ruleId: 9, depth: 1, nucleusId: 1, atomIds: [2, 3], freshAtomIds: [2],
    decisionEvidence: { markingScore: .8, sharedSites: 1, emittedSites: 1, targetUsed: false } },
];
const audit = buildSiteProvenance({ atom: atoms[1], atoms, placements,
  sceneToAngstrom: 2, neighborReachScene: 1.1, geometryLabel: "lattice" });
assert.equal(audit.origin, "GCTS-emitted structural site");
assert.deepEqual(audit.positionAngstrom, [2, 0, 0]);
assert.equal(audit.localEnvironment.coordination, 1);
assert.deepEqual(audit.localEnvironment.speciesCounts, [["Na", 1]]);
assert.equal(audit.localEnvironment.nearest[0].distanceAngstrom, 2);
assert.equal(audit.lineage.creatorClusterId, 2);
assert.equal(audit.lineage.parentClusterId, 1);
assert.equal(audit.lineage.ruleId, 9);
assert.equal(audit.lineage.sharedClusterSite, true);
assert.equal(audit.decisionEvidence.markingScore, .8);
assert.equal(audit.audit.targetUsed, false);
assert.equal(audit.audit.includedInReceipt, false);
const supplied = buildSiteProvenance({ atom: atoms[0], atoms, placements,
  sceneToAngstrom: 2, neighborReachScene: 1.1 });
assert.equal(supplied.origin, "supplied observation / fitted seed");
assert.equal(supplied.observedReferenceIndex, 7);
const angular = buildSiteProvenance({ atom: atoms[0], atoms, placements,
  sceneToAngstrom: 2, neighborReachScene: 2.1 });
assert.deepEqual(angular.localEnvironment.distanceShells, [["Cl", [2]], ["Na", [4]]]);
assert.deepEqual(angular.localEnvironment.angleShells, [["Cl|Na", [90]]]);
assert.throws(() => buildSiteProvenance({ atom: null, atoms, neighborReachScene: 1 }), /required/);
console.log("materials site provenance: passed");
