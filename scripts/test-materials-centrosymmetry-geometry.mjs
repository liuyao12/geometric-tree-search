import assert from "node:assert/strict";
import {
  inferCentrosymmetryNeighborCount,
  localCentrosymmetry,
  optimalCentrosymmetryPairing,
} from "../apps/iqc-growth-live/centrosymmetry-geometry.js";

const cubic = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const perfect = optimalCentrosymmetryPairing(cubic, { neighborCount: 6 });
assert.equal(perfect.resolved, true);
assert.equal(perfect.pairs.length, 3);
assert.ok(perfect.rawParameter < 1e-14);
assert.ok(perfect.normalizedAmplitude < 1e-14);

const distorted = cubic.map((vector) => [...vector]);
distorted[0][0] = 1.2;
const distortion = optimalCentrosymmetryPairing(distorted, { neighborCount: 6 });
assert.ok(distortion.rawParameter > 0);
assert.ok(distortion.normalizedAmplitude > 0);

const rotate = ([x, y, z]) => [-y, x, z];
const transformed = distorted.map((vector) => rotate(vector).map((value) => 7.3 * value)).reverse();
const invariant = optimalCentrosymmetryPairing(transformed, { neighborCount: 6 });
assert.ok(Math.abs(invariant.normalizedParameter - distortion.normalizedParameter) < 1e-12);
assert.ok(Math.abs(invariant.normalizedAmplitude - distortion.normalizedAmplitude) < 1e-12);

const surface = optimalCentrosymmetryPairing(cubic.slice(0, 5), { neighborCount: 6 });
assert.equal(surface.resolved, false);
assert.match(surface.reason, /requires 6 neighbors/);

const inferred = inferCentrosymmetryNeighborCount([6, 6, 6, 5, 4, 8], 3);
assert.equal(inferred.selectedNeighborCount, 6);
const distribution = localCentrosymmetry([cubic, distorted, cubic.slice(0, 4)], { neighborCount: 6 });
assert.equal(distribution.resolvedCenters, 2);
assert.equal(distribution.unresolvedCenters, 1);
assert.equal(distribution.histogram.length, 24);
assert.ok(Math.abs(distribution.histogram.reduce((sum, value) => sum + value, 0) - 1) < 1e-12);
assert.equal(distribution.exactOptimalPairing, true);

assert.throws(() => optimalCentrosymmetryPairing(cubic, { neighborCount: 5 }), /even integer/);
assert.throws(() => optimalCentrosymmetryPairing([[0, 0, 0], [1, 0, 0]], { neighborCount: 2 }), /non-zero/);

console.log("materials centrosymmetry geometry: passed");
