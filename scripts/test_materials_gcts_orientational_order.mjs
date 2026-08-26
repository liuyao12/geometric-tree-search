import assert from "node:assert/strict";
import {
  legendrePolynomial,
  localOrientationalOrder,
  orientationalOrderDistribution,
} from "../apps/iqc-growth-live/structure-observables.js";

const close = (first, second, tolerance = 1e-10) =>
  assert.ok(Math.abs(first - second) <= tolerance, `${first} != ${second}`);

close(legendrePolynomial(0, .23), 1);
close(legendrePolynomial(1, .23), .23);
close(legendrePolynomial(2, .23), (3 * .23 ** 2 - 1) / 2);

const hexagon = Array.from({ length: 6 }, (_, index) => {
  const angle = index * Math.PI / 3;
  return [Math.cos(angle), Math.sin(angle), 0];
});
close(localOrientationalOrder([hexagon], 2, { harmonic: 6 })[0], 1);
close(localOrientationalOrder([hexagon], 2, { harmonic: 4 })[0], 0);

const rotatedHexagon = hexagon.map(([x, y, z]) => {
  const angle = .371;
  return [Math.cos(angle) * x - Math.sin(angle) * y,
    Math.sin(angle) * x + Math.cos(angle) * y, z];
});
close(localOrientationalOrder([rotatedHexagon], 2, { harmonic: 6 })[0], 1);

const tetrahedron = [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]];
const q4 = localOrientationalOrder([tetrahedron], 3, { harmonic: 4 })[0];
const q6 = localOrientationalOrder([tetrahedron], 3, { harmonic: 6 })[0];
assert.ok(q4 > .50 && q4 < .52);
assert.ok(q6 > .62 && q6 < .64);

const rotation = ([x, y, z]) => [
  .36 * x - .48 * y + .8 * z,
  .8 * x + .60 * y,
  -.48 * x + .64 * y + .60 * z,
];
close(localOrientationalOrder([tetrahedron.map(rotation)], 3, { harmonic: 4 })[0], q4);
close(localOrientationalOrder([tetrahedron.map(rotation)], 3, { harmonic: 6 })[0], q6);

const octahedron = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
close(localOrientationalOrder([octahedron], 3, { harmonic: 6 })[0], Math.sqrt(1 / 8));

const distribution = orientationalOrderDistribution([0, .25, .5, .75, 1], 4);
close(distribution.histogram.reduce((sum, value) => sum + value, 0), 1);
close(distribution.mean, .5);
close(distribution.median, .5);
close(distribution.highFraction, .4);
assert.equal(distribution.histogram.length, 4);

assert.throws(() => localOrientationalOrder([[[0, 0, 0]]], 4), /dimension/);
assert.throws(() => orientationalOrderDistribution([Number.NaN]), /finite/);

console.log("orientational-order observable: passed");
