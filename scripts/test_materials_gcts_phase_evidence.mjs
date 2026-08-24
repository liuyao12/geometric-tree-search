import assert from "node:assert/strict";
import {
  centeredStructuralWindow,
  inferPointSetDimension,
  phaseComparisonRadius,
} from "../apps/iqc-growth-live/phase-evidence.js";

const rotate = ([x, y, z]) => {
  const angle = .713;
  const cosine = Math.cos(angle); const sine = Math.sin(angle);
  return [cosine * x - sine * z + 8, y - 3, sine * x + cosine * z + 5];
};

const plane = [];
for (let x = -3; x <= 3; x++) for (let y = -3; y <= 3; y++) plane.push({ p: rotate([x, y, 0]) });
const volume = [];
for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) for (let z = -2; z <= 2; z++) volume.push({ p: [x, y, z] });
const bilayer = [];
for (const z of [-1.15, 1.15]) for (let x = -6; x <= 6; x++) for (let y = -6; y <= 6; y++) {
  bilayer.push({ p: rotate([x + .5 * (y % 2), .866 * y, z]) });
}

const planeAudit = inferPointSetDimension(plane);
const volumeAudit = inferPointSetDimension(volume);
const bilayerAudit = inferPointSetDimension(bilayer);
assert.equal(planeAudit.dimension, 2);
assert.ok(planeAudit.planarityRatio < 1e-10);
assert.equal(volumeAudit.dimension, 3);
assert.ok(volumeAudit.planarityRatio > .9);
assert.ok(volumeAudit.localPlanarityRatio > .1);
assert.equal(bilayerAudit.dimension, 2);
assert.ok(bilayerAudit.planarityRatio > .02, "the global audit must see finite layer thickness");
assert.ok(bilayerAudit.localPlanarityRatio < 1e-10, "local geometry must recover the planar sheets");
assert.equal(bilayerAudit.basis, "median local covariance");

const tagged = volume.map((atom, id) => ({ ...atom, id }));
const shifted = tagged.map((atom) => ({ ...atom, p: atom.p.map((value, axis) => value + [13, -7, 4][axis]) }));
assert.deepEqual(centeredStructuralWindow(tagged, 17).map((atom) => atom.id),
  centeredStructuralWindow(shifted, 17).map((atom) => atom.id));
assert.equal(centeredStructuralWindow(tagged, 17).length, 17);

assert.equal(phaseComparisonRadius(1, 2), 1.5);
assert.ok(phaseComparisonRadius(64, 3) > phaseComparisonRadius(8, 3));
assert.equal(phaseComparisonRadius(100000, 3), 3.2);

console.log("matched-window phase evidence geometry: passed", {
  planeRatio: planeAudit.planarityRatio,
  volumeRatio: volumeAudit.planarityRatio,
  bilayerGlobalRatio: bilayerAudit.planarityRatio,
  bilayerLocalRatio: bilayerAudit.localPlanarityRatio,
});
