import assert from "node:assert/strict";
import { chargeMomentSignature, compareChargeMomentGeometry } from "../apps/iqc-growth-live/global-charge-moments.js";

const sites = [
  { position: [-1, 0, 0], charge: 1 }, { position: [1, 0, 0], charge: -1 },
  { position: [0, -1, 0], charge: -1 }, { position: [0, 1, 0], charge: 1 },
  { position: [0, 0, -1], charge: 1 }, { position: [0, 0, 1], charge: -1 },
];
const signature = chargeMomentSignature(sites);
assert.equal(signature.available, true);
assert.equal(signature.siteCount, 6);
assert.equal(signature.netCharge, 0);
assert.ok(Number.isFinite(signature.dipoleMagnitude));
assert.ok(Number.isFinite(signature.quadrupoleMagnitude));

const transform = ([x, y, z]) => [3 * (-y) + 7, 3 * x - 4, 3 * z + 2];
const transformed = [...sites].reverse().map((site) => ({ position: transform(site.position), charge: site.charge }));
const transformedSignature = chargeMomentSignature(transformed);
assert.ok(Math.abs(signature.dipoleMagnitude - transformedSignature.dipoleMagnitude) < 1e-12);
assert.ok(Math.abs(signature.quadrupoleMagnitude - transformedSignature.quadrupoleMagnitude) < 1e-12);

const completion = { position: [0, 0, 2], charge: 1 };
const result = compareChargeMomentGeometry(sites, [completion], "combined");
assert.equal(result.available, true);
assert.equal(result.addedSites, 1);
assert.ok(result.score >= -1 && result.score <= 1);
assert.equal(result.translationInvariant, true);
assert.equal(result.properRotationInvariant, true);
assert.equal(result.uniformScaleInvariant, true);
assert.equal(result.candidateGeometryChanged, false);
assert.equal(result.targetUsed, false);
assert.equal(result.electrostaticEnergyInferred, false);
assert.equal(result.electronicStructureModeled, false);

assert.equal(compareChargeMomentGeometry([], [completion], "dipole").available, false);
assert.equal(compareChargeMomentGeometry(sites, [], "dipole").available, false);
assert.equal(chargeMomentSignature([{ position: [0, 0, 0], charge: 0 }]).available, false);

console.log("global charge moments: passed");
