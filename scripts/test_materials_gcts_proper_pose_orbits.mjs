import assert from "node:assert/strict";
import { classifyProperPoseOrbits } from "../apps/iqc-growth-live/proper-pose-orbits.js";

const rotate = ([x, y, z]) => [-y, x, z];
const transform = (points, rotation = (point) => point, shift = [0, 0, 0]) => points.map((point) =>
  rotation(point).map((value, axis) => value + shift[axis]));
const water = [[0, 0, 0], [.96, 0, 0], [-.24, .93, 0]];
const occurrence = (positions) => ({ species: ["O", "H", "H"], positions });

const repeated = classifyProperPoseOrbits([
  occurrence(water), occurrence(water), occurrence(transform(water, rotate)), occurrence(transform(water, rotate)),
]);
assert.equal(repeated.orientations, 2);
assert.deepEqual(repeated.populations, [2, 2]);
assert.equal(repeated.support, "finite required set");
assert.equal(repeated.frameKind, "right-handed intrinsic frame");

const globallyMoved = classifyProperPoseOrbits([
  occurrence(transform(water, rotate, [4, -2, 7])),
  occurrence(transform(water, rotate, [4, -2, 7])),
  occurrence(transform(transform(water, rotate), rotate, [4, -2, 7])),
  occurrence(transform(transform(water, rotate), rotate, [4, -2, 7])),
]);
assert.equal(globallyMoved.orientations, repeated.orientations);
assert.deepEqual(globallyMoved.populations, repeated.populations);
assert.equal(globallyMoved.commonProperRotationEquivariant, true);
assert.equal(globallyMoved.improperRotationsQuotiented, false);

const atom = classifyProperPoseOrbits([
  { species: ["Na"], positions: [[0, 0, 0]] },
  { species: ["Na"], positions: [[5, 2, -1]] },
]);
assert.equal(atom.orientations, 1);
assert.equal(atom.frameKind, "orientation-invisible support");

const octahedron = [[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
const rocksalt = classifyProperPoseOrbits([
  { species: ["Na", "Cl", "Cl", "Cl", "Cl", "Cl", "Cl"], positions: octahedron },
  { species: ["Na", "Cl", "Cl", "Cl", "Cl", "Cl", "Cl"], positions: transform(octahedron, rotate) },
]);
assert.equal(rocksalt.orientations, 1);
assert.equal(rocksalt.properSymmetryGaugeCount, 24);

const chiral = [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]];
const mirror = chiral.map(([x, y, z]) => [-x, y, z]);
const handed = classifyProperPoseOrbits([
  { species: ["A", "B", "C", "D"], positions: chiral },
  { species: ["A", "B", "C", "D"], positions: mirror },
]);
assert.equal(handed.orientations, 2);
assert.equal(handed.improperRotationsQuotiented, false);

assert.throws(() => classifyProperPoseOrbits([
  occurrence(water), { species: ["O"], positions: [[0, 0, 0]] },
]), /fixed topology/);

console.log("proper pose orbit tests passed");
