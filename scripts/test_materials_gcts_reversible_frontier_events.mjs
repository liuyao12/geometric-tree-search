import assert from "node:assert/strict";
import { detachableLeafPlacementAudit, enumerateDetachableLeafPlacements }
  from "../apps/iqc-growth-live/reversible-frontier-events.mjs";

const placements = [
  { id: 1, seedNucleus: true, parentId: null, nucleusId: 1, atomIds: [1, 2], freshAtomIds: [] },
  { id: 2, parentId: 1, nucleusId: 1, ruleId: 7, atomIds: [1, 2, 3, 4], freshAtomIds: [3, 4] },
];
const atoms = [
  { id: 1, clusterIds: [1, 2], nucleusIds: [1] },
  { id: 2, clusterIds: [1, 2], nucleusIds: [1] },
  { id: 3, clusterIds: [2], nucleusIds: [1], createdByClusterId: 2 },
  { id: 4, clusterIds: [2], nucleusIds: [1], createdByClusterId: 2 },
];
const leaf = detachableLeafPlacementAudit(placements[1], placements, atoms);
assert.equal(leaf.admitted, true);
assert.deepEqual(leaf.removableAtomIds, [3, 4]);
assert.deepEqual(leaf.retainedSharedAtomIds, [1, 2]);
assert.equal(leaf.sharedAtomsDeleted, false);

const withChild = [...placements,
  { id: 3, parentId: 2, nucleusId: 1, atomIds: [3, 4, 5], freshAtomIds: [5] }];
assert.match(detachableLeafPlacementAudit(placements[1], withChild, atoms).reasons.join(" "), /dependent/);
const sharedCreated = atoms.map((atom) => atom.id === 3 ? { ...atom, clusterIds: [2, 9] } : atom);
assert.match(detachableLeafPlacementAudit(placements[1], placements, sharedCreated).reasons.join(" "), /shared/);
assert.equal(detachableLeafPlacementAudit({ ...placements[1], reconstructionOnly: true }, placements, atoms).admitted, false);

const catalog = enumerateDetachableLeafPlacements({ placements, atoms });
assert.deepEqual(catalog.admitted.map((audit) => audit.placementId), [2]);
assert.equal(catalog.targetUsed, false);
assert.equal(catalog.sharedAtomsRetained, true);

console.log("reversible frontier event ownership: passed");
