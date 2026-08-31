import assert from "node:assert/strict";
import { buildHierarchyEvidenceMicroscope, hierarchyEvidenceReceiptIds }
  from "../apps/iqc-growth-live/hierarchy-evidence-microscope.mjs";

assert.deepEqual(hierarchyEvidenceReceiptIds(), [
  "iqc-reencoding", "iqc-compression", "cdyb-transfer", "nacl-stationary",
]);

const iqc = buildHierarchyEvidenceMicroscope("iqc-reencoding");
assert.equal(iqc.schema, "gcts-hierarchy-evidence-microscope-v1");
assert.equal(iqc.totalAtoms, 1248);
assert.deepEqual(iqc.levels.map((level) => level.activeTypes), [148, 10, 4, 1]);
assert.deepEqual(iqc.levels.map((level) => level.coveredAtoms), [1220, 1033, 925, 870]);
assert.deepEqual(iqc.levels.map((level) => level.residualAtoms), [28, 215, 323, 378]);
assert.equal(iqc.levels[2].supportAmplificationFromPrevious, 110 / 78);
assert.equal(iqc.highestProvenClaim.id, "reencoding");
assert.equal(iqc.stationaryCommonKeys, 0);
assert.equal(iqc.exponentialClaimed, false);
assert.equal(iqc.heldoutCoordinatesObservedForMatching, true);

const compression = buildHierarchyEvidenceMicroscope("iqc-compression");
assert.deepEqual(compression.levels.map((level) => level.activeTypes), [73, 17, 6, 3, 2, 1]);
assert.equal(compression.highestProvenClaim.id, "recurring");
assert.ok(compression.levels.every((level) => level.coveredAtoms + level.residualAtoms === 2064));

const cdyb = buildHierarchyEvidenceMicroscope("cdyb-transfer");
assert.deepEqual(cdyb.levels.map((level) => [level.frozenTypes, level.activeTypes]), [
  [80, 53], [36, 20], [22, 8], [15, 2], [8, 0],
]);
assert.equal(cdyb.levels.at(-1).residualFraction, 1);
assert.equal(cdyb.highestProvenClaim.id, "reencoding");

const nacl = buildHierarchyEvidenceMicroscope("nacl-stationary");
assert.equal(nacl.stationaryCommonKeys, 1);
assert.equal(nacl.representedAfterSevenActions, 4194304);
assert.equal(nacl.highestProvenClaim.id, "stationary");
assert.equal(nacl.exponentialClaimed, true);
assert.equal(nacl.claimLadder.find((rung) => rung.id === "autonomous").passed, false);

assert.throws(() => buildHierarchyEvidenceMicroscope("unknown"), /Unknown hierarchy evidence receipt/);

console.log("hierarchy evidence microscope model passed");

