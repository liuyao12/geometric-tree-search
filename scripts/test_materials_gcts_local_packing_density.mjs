import assert from "node:assert/strict";
import { localPackingDensityAudit } from "../apps/iqc-growth-live/local-packing-density.js";

const cube = [];
for (let x = -2; x <= 2; x++) for (let y = -2; y <= 2; y++) for (let z = -2; z <= 2; z++) cube.push([x, y, z]);
const transform = ([x, y, z]) => [3 + 2 * (-y), -4 + 2 * x, 7 + 2 * z];
const transformed = cube.map(transform).reverse();
const reference = localPackingDensityAudit(cube, cube);
const invariant = localPackingDensityAudit(transformed, transformed);
assert.equal(reference.available, true);
assert.equal(reference.neighborRank, 6);
assert.ok(Math.abs(reference.medianRelativeDensity - 1) < 1e-12);
assert.ok(Math.abs(invariant.medianRelativeDensity - reference.medianRelativeDensity) < 1e-12);
assert.ok(Math.abs(invariant.coreMedianRelativeDensity - reference.coreMedianRelativeDensity) < 1e-12);
assert.deepEqual(invariant.histogram, reference.histogram);

const expanded = cube.map(([x, y, z]) => [1.25 * x, 1.25 * y, 1.25 * z]);
const openAudit = localPackingDensityAudit(expanded, cube);
assert.ok(openAudit.medianRelativeDensity < .7);
assert.ok(openAudit.medianRelativeLocalVolume > 1.8);
assert.equal(openAudit.massDensityInferred, false);
assert.equal(openAudit.porosityInferred, false);
assert.equal(openAudit.targetUsed, false);
console.log("local packing-density invariants: passed");
