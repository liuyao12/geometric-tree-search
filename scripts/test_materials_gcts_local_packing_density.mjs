import assert from "node:assert/strict";
import { localPackingDensityAudit } from "../apps/iqc-growth-live/local-packing-density.js";

const cube = [];
for (let x = -3; x <= 3; x++) for (let y = -3; y <= 3; y++) for (let z = -3; z <= 3; z++) cube.push([x, y, z]);
const cubeSpecies = cube.map(([x, y, z]) => {
  const radius = Math.sqrt(x * x + y * y + z * z);
  return radius > 4 ? "B" : radius < 2.5 ? "A" : "C";
});
const transform = ([x, y, z]) => [3 + 2 * (-y), -4 + 2 * x, 7 + 2 * z];
const transformed = cube.map(transform).reverse();
const reference = localPackingDensityAudit(cube, cube, { currentSpecies: cubeSpecies, referenceSpecies: cubeSpecies });
const invariant = localPackingDensityAudit(transformed, transformed, {
  currentSpecies: [...cubeSpecies].reverse(), referenceSpecies: [...cubeSpecies].reverse(),
});
assert.equal(reference.available, true);
assert.equal(reference.neighborRank, 6);
assert.ok(Math.abs(reference.coreMedianRelativeDensity - 1) < 1e-12);
assert.ok(Math.abs(invariant.medianRelativeDensity - reference.medianRelativeDensity) < 1e-12);
assert.ok(Math.abs(invariant.coreMedianRelativeDensity - reference.coreMedianRelativeDensity) < 1e-12);
assert.deepEqual(invariant.histogram, reference.histogram);
assert.deepEqual(invariant.radialProfile, reference.radialProfile);
assert.equal(reference.radialProfile.length, 8);
assert.deepEqual(reference.speciesVocabulary, ["A", "B", "C"]);
reference.radialProfile.filter((shell) => shell.siteCount).forEach((shell) => assert.ok(
  Math.abs(Object.values(shell.speciesFractions).reduce((sum, value) => sum + value, 0) - 1) < 1e-12));
assert.equal(reference.dominantSurfaceExcessSpecies, "B");
assert.ok(reference.surfaceExcess.B > 0);
assert.ok(reference.sampledCenters > 128, "complete equal-radius ties must not be split by input order");

const expanded = cube.map(([x, y, z]) => [1.25 * x, 1.25 * y, 1.25 * z]);
const openAudit = localPackingDensityAudit(expanded, cube, { currentSpecies: cubeSpecies, referenceSpecies: cubeSpecies });
assert.ok(openAudit.medianRelativeDensity < .7);
assert.ok(openAudit.medianRelativeLocalVolume > 1.8);
assert.equal(openAudit.massDensityInferred, false);
assert.equal(openAudit.porosityInferred, false);
assert.equal(openAudit.targetUsed, false);
console.log("local packing-density invariants: passed");
